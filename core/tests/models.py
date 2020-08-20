import os
from unittest.mock import MagicMock, Mock

from bson import ObjectId
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

import core
from core.exceptions import WrongFileType, WrongAction
from core.models import DatatableActionType, DatatableAction
from core.models.datatable import DatatableMongoClient
from core.tests.factories.models import DatatableFactory, DatatableActionFactory
from core.tests.mocks import MockCollection, MockClient

User = get_user_model()


class DatatableTestCase(TestCase):
    fixtures = ['initial_groups.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='Test')

    def test_upload_datatable_file(self):
        """
        Tests if file is passed to MongoClient method
        """
        instance = DatatableFactory()
        instance.client.upload_file_to_db = MagicMock()
        client_upload_function = instance.client.upload_file_to_db
        instance.upload_datatable_file(file=b'test_file')

        client_upload_function.assert_called_once_with(b'test_file')

    def test_register_action(self):
        instance = DatatableFactory()

        instance.register_action(self.user, DatatableActionType.CREATE.value,
                                 old_row={'old_key': 'old_val'},
                                 new_row={'new_key': 'new_val'})

        action = DatatableAction.objects.get(datatable=instance)
        self.assertEqual(action.datatable, instance)

    def test_repr(self):
        instance = DatatableFactory(title='test')
        self.assertEqual(repr(instance), 'test')


class DatatableMongoClientTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mock_collection = MockCollection()
        cls.instance = DatatableMongoClient('collection', MagicMock(
            return_value={settings.MONGO_DATABASE: MagicMock(
                return_value={'collection': cls.mock_collection})}))

        # ObjectId compliant value
        cls.binary_id = '0123456789ab0123456789ab'

    def test_get_rows(self):
        self.instance.get_rows()
        self.instance.collection.find.assert_called_with({})

        self.instance.get_rows({'column': 'value'})
        self.instance.collection.find.assert_called_with({'column': 'value'})

    def test_has_row_true(self):
        """
        Tests if instance return True if count returned positive value
        """
        self.instance.collection.count_documents.return_value = 1
        result = self.instance.has_row(row_id=self.binary_id)
        self.instance.collection.count_documents.assert_called_with({'_id': ObjectId(self.binary_id)})
        self.assertTrue(result)

    def test_has_row_false(self):
        """
        Tests if instance return False if count returned 0
        """
        self.instance.collection.count_documents.return_value = 0
        result = self.instance.has_row(row_id=self.binary_id)
        self.instance.collection.count_documents.assert_called_with({'_id': ObjectId(self.binary_id)})
        self.assertFalse(result)

    def test_add_row(self):
        """
        Tests if insert_one was called with specified params
        """
        self.instance.add_row({'column': 'value'})
        self.instance.collection.insert_one.assert_called_with({'column': 'value'})

        self.instance.add_row({'column': 'value'}, row_id=self.binary_id)
        self.instance.collection.insert_one.assert_called_with({'column': 'value',
                                                                '_id': ObjectId(self.binary_id)})

    def test_patch_row(self):
        self.instance.patch_row(self.binary_id, {'column': 'value'})
        self.instance.collection.update_one.assert_called_with({'_id': ObjectId(self.binary_id)},
                                                               {'$set': {'column': 'value'}})

    def test_delete_row(self):
        self.instance.delete_row(self.binary_id)
        self.instance.collection.delete_one.assert_called_with({'_id': ObjectId(self.binary_id)})

    def test_upload_file_to_db_csv(self):
        file = Mock()
        file.content_type = 'text/csv'
        self_path = os.path.dirname(core.__file__)
        with open(os.path.join(self_path, 'tests/data_samples/csv.csv'), 'rb') as csv_file:
            file.file = csv_file

            self.instance.upload_file_to_db(file)
        self.instance.collection.insert_many.assert_called_with([{'str_col': 'str_1',
                                                                  'int_col': 1},
                                                                 {'str_col': 'str_2',
                                                                  'int_col': 2}])

    def test_upload_file_to_db_excel(self):
        file = Mock()
        file.content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        self_path = os.path.dirname(core.__file__)
        with open(os.path.join(self_path, 'tests/data_samples/excel.xlsx'), 'rb') as excel_file:
            file.file = excel_file

            self.instance.upload_file_to_db(file)
        self.instance.collection.insert_many.assert_called_with(
            [{'str_col': 'str_1', 'int_col': 1, 'date_col': '2020-01-01'},
             {'str_col': 'str_2', 'int_col': 2, 'date_col': '2020-01-08'}])

    def test_upload_file_to_db_wrong_filetype(self):
        file = Mock()
        file.content_type = 'wrong/filetype'

        with self.assertRaises(WrongFileType):
            self.instance.upload_file_to_db(file)


class DatatableActionTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.instance = DatatableActionFactory()
        cls.instance.datatable.client = MockClient()

    def test_revert_action_create(self):
        self.instance.action = DatatableActionType.CREATE.value
        self.instance.revert_action()

        self.instance.datatable.client.delete_row.assert_called_with(self.instance.new_row['_id'])
        self.assertTrue(self.instance.reverted)

    def test_revert_action_delete(self):
        self.instance.action = DatatableActionType.DELETE.value
        self.instance.revert_action()

        self.instance.datatable.client.add_row.assert_called_with(self.instance.old_row,
                                                                  row_id=self.instance.old_row['_id'])
        self.assertTrue(self.instance.reverted)

    def test_revert_action_update(self):
        self.instance.action = DatatableActionType.UPDATE.value
        self.instance.revert_action()

        self.instance.datatable.client.patch_row.assert_called_with(self.instance.old_row['_id'],
                                                                    self.instance.old_row)
        self.assertTrue(self.instance.reverted)

    def test_revert_action_wrong_action(self):
        self.instance.action = 'WRONG'

        with self.assertRaises(WrongAction):
            self.instance.revert_action()
