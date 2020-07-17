import csv
import os
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from pyDataverse.api import Api
from requests import ConnectionError
from rest_framework import serializers

from core.models import Datatable


class DatatableReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Datatable
        fields = ['id', 'title', 'collection_name']
        read_only_fields = fields


class DatatableSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)

    class Meta:
        model = Datatable
        exclude = ['columns']

    def validate_file(self, file: InMemoryUploadedFile):
        """
        Checks if file content-type is supported
        :param file:
        """
        if file.content_type not in settings.SUPPORTED_MIME_TYPES:
            raise serializers.ValidationError('Unsupported file type.')
        return file

    def create(self, validated_data):
        """
        Creates datatable metadata and uploads file as datable content
        :param validated_data:
        :return: datatable instance
        """
        file = validated_data.pop('file')
        with transaction.atomic():
            result = super().create(validated_data)
            result.upload_datatable_file(file)
        return result


class DatatableExportSerializer(serializers.ModelSerializer):
    dataset_pid = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Datatable
        fields = ['id', 'title', 'collection_name', 'dataset_pid']
        read_only_fields = fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = Api(base_url=settings.DATAVERSE_URL,
                          api_token=settings.DATAVERSE_ACCESS_TOKEN)

    def validate_dataset_pid(self, dataset_pid):
        if self.client.status != 'OK':
            raise serializers.ValidationError('Can\'t connect to Dataverse server.')

        try:
            dataset = self.client.get_dataset(dataset_pid)
        except ConnectionError:
            raise serializers.ValidationError(f'Can\'t find Dataset {dataset_pid} in Dataverse.')

        if not dataset:
            raise serializers.ValidationError('Dataset doesn\'t exist in Dataverse.')

        return dataset_pid

    def export(self, cursor):
        # Create temp directory if doesn't exist
        Path(settings.TMP_MEDIA_PATH).mkdir(parents=True, exist_ok=True)

        tmp_file_name = os.path.join(settings.TMP_MEDIA_PATH, self.instance.title + '.csv')
        try:
            with open(tmp_file_name, 'w') as file:
                dict_writer = csv.DictWriter(file, ['_id', *self.instance.columns.keys()])
                dict_writer.writeheader()
                dict_writer.writerows(cursor)

            identifier = self.validated_data['dataset_pid']
            result = self.client.upload_file(identifier, tmp_file_name)
            if result['status'] == 'OK':
                result = self.client.publish_dataset(identifier, type='major')
        finally:
            os.remove(tmp_file_name)

        return result
