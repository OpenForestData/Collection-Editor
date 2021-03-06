from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from datetime import datetime
from io import StringIO, BytesIO
from typing import Type

import numpy
import pandas as pd
from bson import ObjectId
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
# Type imports for Docs
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models, transaction
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult

from core.exceptions import WrongFileType
from core.models.datatable_action import DatatableAction, DatatableActionType


class DatatableClient(ABC):
    """
    Interface for Datatable Client.
    """

    @abstractmethod
    def get_rows(self, query: dict = None):
        """
        Returns rows form given DB based on query
        """

    @abstractmethod
    def has_row(self, row_id: str):
        """
        Adds rows form given DB based on data
        """

    @abstractmethod
    def add_row(self, data: dict, row_id: str = None):
        """
        Adds rows form given DB based on data
        """

    @abstractmethod
    def patch_row(self, row_id: str, data: dict):
        """
        Updates row specified by id with data
        """

    @abstractmethod
    def delete_row(self, row_id: str):
        """
        Deletes row specified by id
        """

    @abstractmethod
    def upload_file_to_db(self, file: InMemoryUploadedFile):
        """
        Upload given file as rows of a new table in DB
        """


class DatatableMongoClient(DatatableClient):
    """
    MongoDB client for Datatable model
    """

    def __init__(self, collection_name: str, mongo_client: Type[MongoClient] = MongoClient):
        db = mongo_client(
            host=settings.MONGO_HOST,
            port=settings.MONGO_PORT,
            username=settings.MONGO_USER,
            password=settings.MONGO_PASSWORD,
            connect=True
        )[settings.MONGO_DATABASE]
        self.collection: Collection = db[collection_name]
        self.columns = []

    def get_rows(self, query: dict = None) -> Cursor:
        """
        Queries MongoDB datatable

        :param query: MongoDB query
        :return: MongoDB cursor with rows returned by query or all rows if query wasn't specified
        """
        return self.collection.find(query if query else {})

    def has_row(self, row_id: str) -> bool:
        """
        Checks if row with given id exists

        :param row_id: BSON compliant row id
        :return: True if datatable has row with specified id, False otherwise
        """
        return bool(self.collection.count_documents({'_id': ObjectId(row_id)}))

    def add_row(self, data: dict, row_id: str = None) -> InsertOneResult:
        """
        Creates row in datatable

        :param data: MongoDB structured (json) new row data
        :param row_id: BSON compliant unique id that new row should have
        :return: MongoDB insert one result
        """
        data.pop('_id', None)
        if row_id:
            data['_id'] = ObjectId(row_id)
        result = self.collection.insert_one(data)
        return result

    def patch_row(self, row_id: str, data: dict) -> UpdateResult:
        """
        Updates row in datatable

        :param data: MongoDB structured (json) new row data
        :param row_id: BSON compliant row id of row to be updated
        :return: MongoDB update result
        """
        data.pop('_id', None)
        return self.collection.update_one({'_id': ObjectId(row_id)}, {'$set': data})

    def delete_row(self, row_id: str) -> DeleteResult:
        """
        Deletes row in datatable

        :param row_id: id of row to be deleted
        :return: MongoDB delete result
        """
        return self.collection.delete_one({'_id': ObjectId(row_id)})

    def upload_file_to_db(self, file: InMemoryUploadedFile):
        """
        Load file to as a collection of given database

        :param file: request file in *csv* or *xlsx* format to be uploaded to MongoDB
        """
        try:
            file_type = settings.SUPPORTED_MIME_TYPES[file.content_type]
        except KeyError:
            raise WrongFileType(f'File with content-type {file.content_type} is unsupported.')

        if file_type == 'csv':
            in_memory_file = StringIO(file.file.read().decode('utf-8'))
        else:
            in_memory_file = BytesIO(file.file.read())

        # drop datatable if exists
        self.collection.delete_many({})

        if file_type == 'csv':
            # CSV can be loaded in chunks
            delimiter = self.__get_csv_delimiter(file)

            chunk = None
            for chunk in pd.read_csv(in_memory_file, chunksize=2048, sep=delimiter):
                payload = json.loads(chunk.to_json(orient='records', date_format='iso'))
                self.collection.insert_many(payload)
            self.columns = list(chunk.columns)
        else:  # file_type == 'excel'
            loaded_file = pd.read_excel(in_memory_file)
            columns = self.__get_string_converter_for_datetime_columns(loaded_file)
            for column in columns:
                if self.__if_date_column(loaded_file[column]):
                    loaded_file[column] = loaded_file[column].dt.strftime('%Y-%m-%d')

            self.collection.insert_many(json.loads(loaded_file.to_json(orient='records', date_format='iso')))
            self.columns = list(loaded_file.columns)

    @staticmethod
    def __get_csv_delimiter(file):
        file.file.seek(0)
        chunk = file.file.readline().decode('utf-8')
        file.file.seek(0)

        return csv.Sniffer().sniff(chunk).delimiter

    @staticmethod
    def __if_date_column(column):
        zero_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).time()
        return all(list(map(lambda x: x.time() == zero_time, column)))

    @staticmethod
    def __get_string_converter_for_datetime_columns(df: pd.Dataframe):
        return list(df.columns[df.dtypes == numpy.dtype(numpy.datetime64('2000-01-01T00:00:00.000000000'))])


class Datatable(models.Model):
    """
    Datable model representing uploaded tabular files
    """

    #: Title of a datatable
    title = models.CharField(max_length=255)

    #: Name of database table containing datatable rows (has to be unique)
    collection_name = models.CharField(max_length=255, unique=True)

    #: List of existing column names
    columns = ArrayField(models.TextField(blank=True), blank=True, null=True)

    def save(self, *args, **kwargs):
        """
        Saves Datatable metadata to database
        """
        self.__set_database_client()
        super().save(*args, **kwargs)

    @classmethod
    def from_db(cls, db, field_names, values) -> Datatable:
        """
        Overrides parent function to attach NoSQL client at load from DB

        :return: instance of Datatable loaded from database
        """
        instance: Datatable = super().from_db(db, field_names, values)
        instance.__set_database_client()
        return instance

    def upload_datatable_file(self, file: InMemoryUploadedFile):
        """
        Upload file to database table using attached client

        :param file: file to upload
        """
        with transaction.atomic():
            self.client.upload_file_to_db(file)
            self.columns = self.client.columns
            self.save()

    def register_action(self, user, action: DatatableActionType, old_row: dict = None,
                        new_row: dict = None) -> DatatableAction:
        """
        Register action committed on this Datatable to history

        :return: created action model
        """
        return DatatableAction.objects.create(user=user,
                                              action=action,
                                              datatable=self,
                                              old_row=old_row,
                                              new_row=new_row)

    def __set_database_client(self, client: Type[DatatableClient] = DatatableMongoClient):
        """
        Attaches DatatableClient client to self instance based on ``self.collection_name``
        :param client:
        """
        self.client = client(self.collection_name)

    def __str__(self):
        return self.title

    def __repr__(self):
        return str(self)

    class Meta:
        ordering = ['-id']

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
