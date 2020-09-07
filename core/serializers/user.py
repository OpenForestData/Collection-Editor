from django.contrib.auth.models import User
from rest_framework import serializers


class MinimalUserSerializer(serializers.ModelSerializer):
    """
    Serializer for basic User data
    """

    groups = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['pk', 'username', 'first_name', 'last_name', 'groups']
        read_only_fields = fields

    def get_groups(self, user):
        return user.groups.all().values_list('name')

