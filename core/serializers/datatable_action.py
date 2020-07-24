from rest_framework import serializers

from core.models import DatatableAction


class DatatableActionReadOnlySerializer(serializers.ModelSerializer):
    """
    DatatableAction serializer for read-write operations
    """

    class Meta:
        model = DatatableAction
        fields = '__all__'
        read_only_fields = [fields]
