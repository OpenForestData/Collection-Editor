from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
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
