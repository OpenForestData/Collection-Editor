from collections import OrderedDict
from copy import deepcopy

from bson import ObjectId
from django.db import transaction
from rest_framework import serializers

from core.models import DatatableActionType, Datatable


class DatatableRowsReadOnlySerializer(serializers.Serializer):
    """
    Serializer for datatable rows read only actions.
    """
    class Meta:
        model = Datatable

    def to_representation(self, instance: Datatable):
        """
        Skips converting default fields as only specifically stored row should be returned by this serializer.

        :param instance: Datatable to read rows from
        :return: serialized values of instance fields
        """
        ret = OrderedDict()
        for key, val in instance.items():
            ret[key] = str(val)

        return ret


class DatatableRowsSerializer(serializers.Serializer):
    """
    Serializer for datatable rows creation, edition and deletion
    """

    # Add Meta class for permissions
    class Meta:
        model = Datatable

    def is_valid(self, raise_exception: bool=False) -> bool:
        """
        Validates if data passed to serializer contains at least one column value for a row.

        :raise ValidationError: there is no column value in supplied parameters
        :param raise_exception: switch raising exception during validation
        :return: True if serializer is valid, False otherwise
        """
        result = super().is_valid(raise_exception)
        if not self._validated_data and raise_exception:
            raise serializers.ValidationError(
                {'non_field_errors': 'To create or patch a row at least one column has to be specified.'}
            )
        return result

    @property
    def _writable_fields(self):
        """
        Yields Datatable columns as valid writable fields
        """
        for column in self.instance.columns:
            field = serializers.CharField(required=False)
            field.field_name = column
            field.source_attrs = [column]
            yield field

    def add_row(self) -> Datatable:
        """
        Adds row to datatable based on data supplied to serializer and logs this operation as DatatableAction instance.

        :return: Datatable row was added to
        """
        with transaction.atomic():
            row = self.instance.client.add_row(self.validated_data)

            new_row = self.validated_data
            new_row['_id'] = str(row.inserted_id)

            self.instance.register_action(
                self.context['request'].user,
                DatatableActionType.CREATE.value,
                new_row=self.validated_data
            )
        return self.instance

    def patch_row(self, row_id: str):
        """
        Updates row in datatable based on data supplied to serializer and logs this operation as DatatableAction
        instance.

        :param row_id: BSON compliant id of row to be updated
        :return: Datatable row was updated in
        """
        with transaction.atomic():
            old_row = self.instance.client.get_rows({'_id': ObjectId(row_id)})[0]
            self.instance.client.patch_row(row_id, self.validated_data)

            old_row['_id'] = str(old_row['_id'])

            new_row = deepcopy(old_row)
            for key, value in self.validated_data.items():
                new_row[key] = value

            self.instance.register_action(
                self.context['request'].user,
                DatatableActionType.UPDATE.value,
                new_row=new_row,
                old_row=old_row
            )

    def delete_row(self, row_id):
        """
        Deletes row from datatable based on data supplied to serializer and logs this operation as DatatableAction
        instance.

        :param row_id: BSON compliant id of row to be updated
        :return: Datatable row was deleted from
        """
        with transaction.atomic():
            old_row = self.instance.client.get_rows({'_id': ObjectId(row_id)})[0]
            self.instance.client.delete_row(row_id)

            old_row['_id'] = str(old_row['_id'])

            self.instance.register_action(
                self.context['request'].user,
                DatatableActionType.DELETE.value,
                old_row=old_row
            )
