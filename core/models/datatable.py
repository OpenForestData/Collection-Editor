import json
from abc import ABC, abstractmethod
from io import StringIO, BytesIO

import pandas as pd
from bson import ObjectId
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.utils.text import slugify
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor

from core.exceptions import WrongFileType
from core.models.datatable_action import DatatableAction, DatatableActionType


class DatatableClient(ABC):
    """
    Interface for Datable Client.
    """

    @abstractmethod
    def get_rows(self, query: dict = None):
        pass

    @abstractmethod
    def add_row(self, data: dict):
        pass

    @abstractmethod
    def patch_row(self, row_id: str, data: dict):
        pass

    @abstractmethod
    def delete_row(self, row_id: str):
        pass

    @abstractmethod
    def upload_file_to_db(self, filepath: str):
        pass


class DatatableMongoClient(DatatableClient):
    def __init__(self, collection_name: str):
        self.db = MongoClient(
            host=settings.MONGO_HOST,
            port=settings.MONGO_PORT,
            username=settings.MONGO_USER,
            password=settings.MONGO_PASSWORD,
            connect=True
        )[settings.MONGO_DATABASE]
        self.collection: Collection = self.db[collection_name]
        self.columns = {}

    def get_rows(self, query: dict = None) -> Cursor:
        """
        Queries MongoDB datatable
        :param query: MongoDB query
        """
        return self.collection.find(query if query else {})

    def has_row(self, row_id) -> bool:
        """
        Checks if row with given id exists
        :param row_id:
        :return:
        """
        return bool(self.collection.count_documents({'_id': ObjectId(row_id)}))

    def add_row(self, data: dict, row_id: str = None):
        """
        Creates row in datatable
        :param data: json formatted data
        :param row_id: optional if _id should be forced
        :return: MongoDB insert result
        """
        data.pop('_id', None)
        if row_id:
            data['_id'] = row_id
        result = self.collection.insert_one(data)
        return result

    def patch_row(self, row_id: str, data: dict):
        """
        Updates row in datatable
        :param data: json formatted data
        :param row_id:
        :return: MongoDB update result
        """
        data.pop('_id', None)
        return self.collection.update_one({'_id': ObjectId(row_id)}, {'$set': data})

    def delete_row(self, row_id: str):
        """
        Deletes row in datatable
        :param row_id:
        :return: MongoDB delete result
        """
        return self.collection.delete_one({'_id': ObjectId(row_id)})

    def upload_file_to_db(self, file):
        """
        Load file to as a collection of given database
        :param file:
        """
        file_type = settings.SUPPORTED_MIME_TYPES[file.content_type]
        if file_type not in ['csv', 'excel']:
            raise WrongFileType(f'File with content-type {file.content_type} is unsupported.')

        if file_type == 'csv':
            in_memory_file = StringIO(file.file.read().decode('utf-8'))
        else:
            in_memory_file = BytesIO(file.file.read())

        # drop datatable if exists
        if in_memory_file:
            self.collection.delete_many({})

        if file_type == 'csv':
            # CSV can be loaded in chunks
            chunk = None
            for chunk in pd.read_csv(in_memory_file, chunksize=2048):
                payload = json.loads(chunk.to_json(orient='records', date_format='iso'))
                self.collection.insert_many(payload)
            self.columns = self.__get_column_types(chunk)
        else:  # file_type == 'excel'
            loaded_file = pd.read_excel(in_memory_file)
            self.collection.insert_many(json.loads(loaded_file.to_json(orient='records', date_format='iso')))
            self.columns = self.__get_column_types(loaded_file)

    def __get_column_types(self, table: pd.DataFrame):
        column_types = {}
        for column in table.columns:
            cell_value = table.iloc[0][column]
            try:
                column_types[column] = type(cell_value.item())
            except AttributeError:
                # cell value is not of a numpy dtype
                # serializing supports only native values
                if not type(cell_value) in [str, int, float, complex, bool]:
                    column_types[column] = str
                else:
                    column_types[column] = type(cell_value)
        return column_types


class Datatable(models.Model):
    title = models.CharField(max_length=255)
    collection_name = models.CharField(max_length=255, unique=True, blank=True)
    columns = JSONField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """
        Saves Datatable metadata to database
        :return:
        """
        if not self.collection_name:
            self.collection_name = slugify(self.title)
        self.__set_database_client()
        self.__serialize_type()
        return super().save(*args, **kwargs)

    @classmethod
    def from_db(cls, db, field_names, values):
        """
        Overrides parent function to attach NoSQL client at load from DB
        :return:
        """
        instance: Datatable = super().from_db(db, field_names, values)
        instance.__set_database_client()
        instance.__deserialize_type()
        return instance

    def upload_datatable_file(self, file):
        """
        Upload file to NoSQL DB as table using attached client
        :param file: file to upload
        :return:
        """
        with transaction.atomic():
            self.client.upload_file_to_db(file)
            self.columns = self.client.columns
            self.save()

    def register_action(self, user, action: DatatableActionType, old_row=None, new_row=None):
        """
        Register action committed on this Datatable to history
        """
        DatatableAction.objects.create(user=user,
                                       action=action,
                                       datatable=self,
                                       old_row=old_row,
                                       new_row=new_row)

    def __set_database_client(self, client=DatatableMongoClient):
        self.client = client(self.collection_name)

    def __str__(self):
        return self.title

    def __repr__(self):
        return str(self)

    def __serialize_type(self):
        if self.columns:
            for column, col_type in self.columns.items():
                self.columns[column] = str(col_type.__name__)

    def __deserialize_type(self):
        for column, col_type in self.columns.items():
            self.columns[column] = eval(col_type)

    # DRY Permissions

    @staticmethod
    def has_read_permission(request):
        return request.user.is_superuser or request.user.groups.filter(name__in=[settings.READONLY_GROUP_NAME,
                                                                                 settings.READWRITE_GROUP_NAME])

    def has_object_read_permission(self, request):
        return self.has_read_permission(request)

    @staticmethod
    def has_write_permission(request):
        return request.user.is_superuser or request.user.groups.filter(name=settings.READWRITE_GROUP_NAME)

    def has_object_write_permission(self, request):
        return self.has_write_permission(request)
