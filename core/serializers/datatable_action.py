from rest_framework import serializers

from core.models import DatatableAction


class DatatableActionReadOnlySerializer(serializers.ModelSerializer):
    """
    DatatableAction serializer for read-write operations
    """

    username = serializers.SerializerMethodField()
    datatable_title = serializers.CharField(source="datatable.title")

    class Meta:
        model = DatatableAction
        fields = '__all__'
        read_only_fields = [fields]

    def get_username(self, obj):
        full_name = f'{obj.user.first_name} {obj.user.last_name}'
        return full_name if full_name.strip() else obj.user.username
