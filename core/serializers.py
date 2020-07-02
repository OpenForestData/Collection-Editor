from collections import OrderedDict

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import SkipField

from core.models import Datatable


class DatatableReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Datatable
        fields = ['id', 'title', 'collection_name']
        read_only_fields = fields


class DatatableSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)

    class Meta:
        model = Datatable
        fields = '__all__'

    def validate_file(self, file: InMemoryUploadedFile):
        if file.content_type not in settings.SUPPORTED_MIME_TYPES:
            raise serializers.ValidationError('Unsupported file type.')
        return file

    def create(self, validated_data):
        file = validated_data.pop('file')
        with transaction.atomic():
            result = super().create(validated_data)
            result.upload_datatable_file(file)
        return result


class DatatableRowsSerializer(serializers.Serializer):

    def to_representation(self, instance):
        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue
            ret[field.field_name] = field.to_representation(attribute)

        for key, val in instance.items():
            ret[key] = str(val)

        return ret

    # def _writable_fields(self):
    #     pass