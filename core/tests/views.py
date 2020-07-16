import os
from unittest.mock import Mock, patch, MagicMock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APITestCase

import core
from core.models import Datatable, DatatableAction
from core.tests.factories.models import DatatableFactory, DatatableActionFactory, UserFactory

User = get_user_model()


class DatatableViewSetTestCase(APITestCase):
    fixtures = ['initial_groups.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.binary_id = '0123456789ab0123456789ab'

    def setUp(self) -> None:
        self.datatable: Datatable = DatatableFactory()

        file = Mock()
        file.content_type = 'text/csv'
        self_path = os.path.dirname(core.__file__)
        with open(os.path.join(self_path, 'tests/data_samples/csv.csv'), 'rb') as csv_file:
            file.file = csv_file
            self.datatable.upload_datatable_file(file)

        self.user = User.objects.create_user(username='Test')
        self.user.groups.add(Group.objects.get(name=settings.READWRITE_GROUP_NAME))
        self.client.force_authenticate(self.user)

    def test_retrieve(self):
        url = reverse('datatable-detail', kwargs={'pk': self.datatable.pk})
        response = self.client.get(url)
        self.assertTrue(response.data['results'])
        self.assertEqual(response.status_code, 200, msg=response.data)

    def test_retrieve_filtered(self):
        url = reverse('datatable-detail', kwargs={'pk': self.datatable.pk})
        response = self.client.get(url, data={'str_col': 'str_1'})
        self.assertEqual(1, response.data['count'])
        self.assertEqual(response.status_code, 200, msg=response.data)

    def test_retrieve_logical_query(self):
        url = reverse('datatable-detail', kwargs={'pk': self.datatable.pk})
        response = self.client.get(url, data={'logical_query': 'and(str_col=str_1, int_col=1)'})
        self.assertEqual(1, response.data['count'])
        self.assertEqual(response.status_code, 200, msg=response.data)

    def test_retrieve_invalid_logical_query(self):
        url = reverse('datatable-detail', kwargs={'pk': self.datatable.pk})
        response = self.client.get(url, data={'logical_query': 'and(invalid_query)'})
        self.assertEqual(2, response.data['count'])
        self.assertEqual(response.status_code, 200, msg=response.data)

    def test_retrieve_ordering(self):
        url = reverse('datatable-detail', kwargs={'pk': self.datatable.pk})
        response = self.client.get(url, data={'ordering': '-int_col,wrong_param'})
        self.assertEqual('2', response.data['results'][0]['int_col'])
        self.assertEqual(response.status_code, 200, msg=response.data)

    def test_retrieve_invalid_ordering(self):
        url = reverse('datatable-detail', kwargs={'pk': self.datatable.pk})
        response = self.client.get(url, data={'ordering': 'wrong_param'})
        self.assertEqual('1', response.data['results'][0]['int_col'])
        self.assertEqual(response.status_code, 200, msg=response.data)

    def test_retrieve_pagination(self):
        url = reverse('datatable-detail', kwargs={'pk': self.datatable.pk})
        response = self.client.get(url, data={'limit': 1})
        self.assertEqual(1, len(response.data['results']))
        self.assertEqual(response.status_code, 200, msg=response.data)

    def test_retrieve_pagination_wrong_offset(self):
        url = reverse('datatable-detail', kwargs={'pk': self.datatable.pk})
        response = self.client.get(url, data={'offset': 3})
        self.assertFalse(response.data['results'])
        self.assertEqual(response.status_code, 200, msg=response.data)

    def test_add_row(self):
        count = len(list(self.datatable.client.get_rows()))

        url = reverse('datatable-add-row', kwargs={'pk': self.datatable.pk})
        response = self.client.post(url, data={'str_col': 'str3'})

        new_count = len(list(self.datatable.client.get_rows()))
        self.assertEqual(count + 1, new_count)
        self.assertEqual(response.status_code, 200, msg=response.data)

    def test_disallow_adding_empty_row(self):
        url = reverse('datatable-add-row', kwargs={'pk': self.datatable.pk})
        response = self.client.post(url, data={})

        self.assertEqual(response.status_code, 400, msg=response.data)

    def test_delete_row(self):
        rows = list(self.datatable.client.get_rows())
        row = rows[0]

        count = len(rows)

        url = reverse('datatable-row', kwargs={'pk': self.datatable.pk,
                                               'row_id': row['_id']})
        response = self.client.delete(url)

        new_count = len(list(self.datatable.client.get_rows()))

        self.assertEqual(count - 1, new_count)
        self.assertEqual(response.status_code, 204, msg=response.data)

    def test_patch_row(self):
        rows = list(self.datatable.client.get_rows())
        row = rows[0]

        url = reverse('datatable-row', kwargs={'pk': self.datatable.pk,
                                               'row_id': row['_id']})
        self.client.patch(url, data={'int_col': 15})

        new_row = self.datatable.client.get_rows({'_id': row['_id']})[0]

        self.assertEqual(new_row['int_col'], '15')

    @patch('core.views.DatatableViewSet.get_serializer')
    def test_export(self, mock_get_serializer):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.export.return_value = {'status': 'OK'}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('datatable-export', kwargs={'pk': self.datatable.pk})
        response = self.client.post(url, data={'dataset_pid': 1})
        self.assertEqual(response.status_code, 200, msg=response.data)

    def test_action_no_row(self):
        url = reverse('datatable-row', kwargs={'pk': self.datatable.pk,
                                               'row_id': self.binary_id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404, msg=response.data)

        url = reverse('datatable-row', kwargs={'pk': self.datatable.pk,
                                               'row_id': self.binary_id})
        response = self.client.patch(url, data={'int_col': 15})
        self.assertEqual(response.status_code, 404, msg=response.data)

    def test_upload_file(self):
        url = reverse('datatable-list')

        self_path = os.path.dirname(core.__file__)
        with open(os.path.join(self_path, 'tests/data_samples/csv.csv'), 'rb') as csv_file:
            response = self.client.post(url, data={'title': 'TestDatatable',
                                                   'file': csv_file}, format='multipart')

            self.assertEqual(response.status_code, 201, msg=response.data)

    def test_upload_unsupported_file(self):
        url = reverse('datatable-list')

        self_path = os.path.dirname(core.__file__)
        with open(os.path.join(self_path, 'tests/data_samples/wrong.tsv'), 'rb') as wrong_file:
            response = self.client.post(url, data={'title': 'WrongFile',
                                                   'file': wrong_file}, format='multipart')

        self.assertEqual(response.status_code, 400, msg=response.data)


class DatatableActionViewSetTestCase(APITestCase):
    fixtures = ['initial_groups.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # ObjectId compliant value
        cls.binary_id = '0123456789ab0123456789ab'
        datatable = DatatableFactory()
        datatable.client.add_row({'_id': cls.binary_id})

        cls.datatable_action: DatatableAction = DatatableActionFactory(action='CREATE',
                                                                       new_row={'_id': cls.binary_id},
                                                                       datatable=datatable)
        cls.datatable_reverted_action: DatatableAction = DatatableActionFactory(action='CREATE',
                                                                                new_row={'_id': cls.binary_id},
                                                                                datatable=datatable,
                                                                                reverted=True)

        cls.user = UserFactory()
        cls.user.groups.add(Group.objects.get(name=settings.READWRITE_GROUP_NAME))

    def test_revert(self):
        self.client.force_authenticate(self.user)
        url = reverse('datatableaction-revert', kwargs={'pk': self.datatable_action.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200, msg=response.data)

    def test_already_revert(self):
        self.client.force_authenticate(self.user)
        url = reverse('datatableaction-revert', kwargs={'pk': self.datatable_reverted_action.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400, msg=response.data)

    def test_retrieve_permissions(self):
        readonly_user = UserFactory()
        readonly_user.groups.add(Group.objects.get(name=settings.READONLY_GROUP_NAME))
        self.client.force_authenticate(readonly_user)
        url = reverse('datatableaction-detail', kwargs={'pk': self.datatable_action.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, msg=response.data)
