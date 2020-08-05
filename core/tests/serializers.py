import os
from unittest.mock import MagicMock

from django.conf import settings
from django.test import TestCase
from requests import ConnectionError
from rest_framework.exceptions import ValidationError

from core.serializers import DatatableSerializer, DatatableExportSerializer


class DatatableSerializerTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.serializer = DatatableSerializer()

    def test_vaildate_file(self):
        file = MagicMock()
        file.content_type = 'wrong/type'
        with self.assertRaises(ValidationError):
            self.serializer.validate_file(file)


class DatatableExportSerializerTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.serializer = DatatableExportSerializer()
        self.serializer.client = MagicMock()
        self.serializer.instance = MagicMock()

    def test_validate_dataset_pid(self):
        self.serializer.client.status = 'OK'
        self.serializer.client.get_dataset.return_value = {'Title': 'Dataset'}
        pid = self.serializer.validate_dataset_pid('dataset_pid')
        self.assertEqual(pid, 'dataset_pid')

    def test_validate_dataset_pid_wrong_pid(self):
        self.serializer.client.status = 'ERROR'
        with self.assertRaises(ValidationError):
            self.serializer.validate_dataset_pid('wrong_pid')

    def test_validate_dataset_pid_dataverse_connection_error(self):
        self.serializer.client.status = 'OK'
        self.serializer.client.get_dataset.side_effect = ConnectionError()

        with self.assertRaises(ValidationError):
            self.serializer.validate_dataset_pid('dataset_pid')

    def test_validate_dataset_pid_missing_dataset(self):
        self.serializer.client.status = 'OK'
        self.serializer.client.get_dataset.return_value = {}
        with self.assertRaises(ValidationError):
            self.serializer.validate_dataset_pid('dataset_pid')

    def test_export(self):
        self.serializer.instance.title = 'Title'
        self.serializer.instance.columns = {'col_1': '', 'col_2': ''}
        self.serializer._validated_data = {'dataset_pid': 'pid'}

        mocked_response = MagicMock()
        mocked_response.ok = True
        self.serializer._upload_file.return_value = mocked_response
        self.serializer.client.publish_dataset.return_value = mocked_response

        result = self.serializer.export([{'col_1': '1', 'col_2': '2'}])
        # self.serializer._upload_file.assert_called_with('pid',
        #                                                 os.path.join(settings.TMP_MEDIA_PATH, 'Title' + '.csv'))
        self.assertTrue(result.ok)

        mocked_response.ok = False
        self.serializer._upload_file.return_value = mocked_response
        result = self.serializer.export([{'col_1': '1', 'col_2': '2'}])
        self.assertFalse(result.ok)
