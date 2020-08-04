import csv
import mimetypes
import os
from io import StringIO
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from pyDataverse.api import Api
from pymongo.cursor import Cursor
from requests import ConnectionError
from rest_framework import serializers

from core.models import Datatable


class DatatableReadOnlySerializer(serializers.ModelSerializer):
    """
    Datatable serializer for read-only operations
    """

    class Meta:
        model = Datatable
        fields = ['id', 'title', 'collection_name']
        read_only_fields = fields


class DatatableSerializer(serializers.ModelSerializer):
    """
    Datatable serializer for read-write operations
    """

    file = serializers.FileField(write_only=True)

    class Meta:
        model = Datatable
        exclude = ['columns']

    def validate_file(self, file: InMemoryUploadedFile) -> InMemoryUploadedFile:
        """
        Checks if file content-type is supported

        :param file: uploaded file
        :return: validated file
        """
        guessed_content_type = mimetypes.guess_type(file.name)

        if file.content_type not in settings.SUPPORTED_MIME_TYPES or \
                guessed_content_type not in settings.SUPPORTED_MIME_TYPES:
            raise serializers.ValidationError(f'Unsupported file type. File is of type {file.content_type}')

        if settings.SUPPORTED_MIME_TYPES[file.content_type] == 'csv':
            chunk = file.file.readline().decode('utf-8')
            file.file.seek(0)

            if not chunk:
                raise serializers.ValidationError(f'File can\'t be empty')

            try:
                dialect = csv.Sniffer().sniff(chunk)

            except csv.Error:
                raise serializers.ValidationError('CSV delimiter can\'t be determined')

            try:
                for _ in pd.read_csv(StringIO(file.file.read().decode('utf-8')), chunksize=2048, sep=dialect.delimiter):
                    pass
            except pd.errors.ParserError as e:
                raise serializers.ValidationError(f'CSV file is corrupted. {e}')

            file.file.seek(0)
        return file

    def create(self, validated_data):
        """
        Creates datatable metadata and uploads file as datable content

        :param validated_data: data validated by serializer
        :return: created Datatable instance
        """
        file = validated_data.pop('file')
        with transaction.atomic():
            result = super().create(validated_data)
            result.upload_datatable_file(file)
        return result


class DatatableExportSerializer(serializers.ModelSerializer):
    """
    Datatable serializer for exporting user uploaded file to database
    """
    dataset_pid = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Datatable
        fields = ['id', 'title', 'collection_name', 'dataset_pid']
        read_only_fields = fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = Api(base_url=settings.DATAVERSE_URL,
                          api_token=settings.DATAVERSE_ACCESS_TOKEN)

    def validate_dataset_pid(self, dataset_pid: str) -> str:
        """
        Validates if:
          -  Dataverse client can connect to Dataverse
          -  supplied dataset pid corresponds to existing Dataset in Dataverse

        :param dataset_pid: Identifier of Dataverse Dataset
        :return: validated Dataset identifier
        """
        if self.client.status != 'OK':
            raise serializers.ValidationError('Can\'t connect to Dataverse server.')

        try:
            dataset = self.client.get_dataset(dataset_pid)
        except ConnectionError:
            raise serializers.ValidationError(f'Can\'t find Dataset {dataset_pid} in Dataverse.')

        if not dataset:
            raise serializers.ValidationError('Dataset doesn\'t exist in Dataverse.')

        return dataset_pid

    def export(self, cursor: Cursor):
        """
        Exports user requested Datatable with applied filters to Dataverse. To do so temporary .csv file is created
        form user submitted Datatable query and uploading said file with Dataverse client.

        Finally temporary file is deleted.

        :param cursor: MongoDB cursor build from user query
        :return: validated Dataset identifier
        """

        # Create temp directory if doesn't exist
        Path(settings.TMP_MEDIA_PATH).mkdir(parents=True, exist_ok=True)

        tmp_file_name = os.path.join(settings.TMP_MEDIA_PATH, self.instance.title + '.csv')
        try:
            with open(tmp_file_name, 'w') as file:
                dict_writer = csv.DictWriter(file, ['_id', *self.instance.columns])
                dict_writer.writeheader()
                dict_writer.writerows(cursor)

            identifier = self.validated_data['dataset_pid']
            result = self.client.upload_file(identifier, tmp_file_name)
            if result['status'] == 'OK':
                result = self.client.publish_dataset(identifier, type='major')
        finally:
            os.remove(tmp_file_name)

        return result
