from enum import Enum

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models

from core.exceptions import WrongAction


class DatatableActionType(Enum):
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'

    @staticmethod
    def choices():
        return [(choice.value, choice.name) for choice in DatatableActionType]


class DatatableAction(models.Model):
    """
    Represents modification made on datatable rows, that was saved to history
    and can be reverted
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    action = models.CharField(choices=DatatableActionType.choices(), null=False, max_length=10)
    datatable = models.ForeignKey('Datatable', on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    old_row = JSONField(null=True)
    new_row = JSONField(null=True)
    reverted = models.BooleanField(default=False)

    def revert_action(self):
        """
        Reverts action based on action type and stored old row
        """
        if self.action == DatatableActionType.DELETE.value:
            self.datatable.client.add_row(self.old_row, row_id=self.old_row['_id'])
            self.set_reverted()
            return
        elif self.action == DatatableActionType.CREATE.value:
            self.datatable.client.delete_row(self.new_row['_id'])
            self.set_reverted()
            return
        elif self.action == DatatableActionType.UPDATE.value:
            self.datatable.client.patch_row(self.old_row['_id'], self.old_row)
            self.set_reverted()
            return

        raise WrongAction(f'Action {self.action} is not proper action')

    def set_reverted(self):
        """
        Sets reverted to True and push it to DB
        """
        self.reverted = True
        self.save(update_fields=['reverted'])

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