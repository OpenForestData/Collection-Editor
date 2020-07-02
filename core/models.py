import json
from abc import ABC, abstractmethod
from io import StringIO

import pandas as pd
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.utils.text import slugify
from pymongo import MongoClient
from pymongo.cursor import Cursor


class DatatableClient(ABC):
    """
    Interface for Datable Client.
    """

    @abstractmethod
    def get_rows(self, query: dict = None):
        """
        Return rows of datatable
        :param query: query to be executed on database
        :return:
        """
        pass

    @abstractmethod
    def add_row(self, data: dict):
        """

        :param data:
        :return:
        """
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
        self.collection = self.db[collection_name]

    def get_rows(self, query: dict = None) -> Cursor:
        return self.collection.find(query if query else {})

    def add_row(self, data: dict):
        pass

    def patch_row(self, row_id: str, data: dict):
        pass

    def delete_row(self, row_id: str):
        pass

    def upload_file_to_db(self, file):
        in_memory_file = StringIO(file.file.read().decode('utf-8'))
        if in_memory_file:
            self.collection.remove()
        for chunk in pd.read_csv(in_memory_file, chunksize=2048):
            if not hasattr(self, 'columns'):
                self.columns = list(chunk.columns)
            payload = json.loads(chunk.to_json(orient='records'))
            self.collection.insert(payload)


class Datatable(models.Model):
    title = models.CharField(max_length=255)
    collection_name = models.CharField(max_length=255, unique=True, blank=True)
    columns = ArrayField(models.CharField(max_length=255, blank=True), blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.collection_name:
            self.collection_name = slugify(self.title)
        self.__set_database_client()
        result = super().save(*args, **kwargs)
        return result

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance.__set_database_client()
        return instance

    def upload_datatable_file(self, file):
        with transaction.atomic():
            self.client.upload_file_to_db(file)
            self.columns = self.client.columns
            self.save()

    def __set_database_client(self, client=DatatableMongoClient):
        self.client = client(self.collection_name)

    def __str__(self):
        return self.title

    def __repr__(self):
        return str(self)
