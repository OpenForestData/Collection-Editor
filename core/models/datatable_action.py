from enum import Enum
from typing import List, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models

from core.exceptions import WrongAction


class DatatableActionType(Enum):
    """
    Types of available actions
    """
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'

    @staticmethod
    def choices() -> List[Tuple[str, str]]:
        """
        Return available action as choices

        :return: Django compliant choices list
        """
        return [(choice.value, choice.name) for choice in DatatableActionType]


class DatatableAction(models.Model):
    """
    Represents modification made on datatable rows, that was saved to history
    and can be reverted
    """

    #: User that committed an action
    user = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    #: Action type
    action = models.CharField(choices=DatatableActionType.choices(), null=False, max_length=10)
    #: Datatable action was committed on
    datatable = models.ForeignKey('Datatable', on_delete=models.CASCADE)

    #: Time of action commitment
    created_at = models.DateTimeField(auto_now_add=True)

    #: State of row before edition/deletion
    old_row = JSONField(null=True)
    #: State of row after edition/creation
    new_row = JSONField(null=True)
    #: Information if action was already reverted
    reverted = models.BooleanField(default=False)

    def revert_action(self):
        """
        Reverts action based on action type and stored old row
        :exception WrongAction: raises when action value is of unimplemented type
        """
        if self.action == DatatableActionType.DELETE.value:
            self.datatable.client.add_row(self.old_row, row_id=self.old_row['_id'])
            self.__set_reverted()
        elif self.action == DatatableActionType.CREATE.value:
            self.datatable.client.delete_row(self.new_row['_id'])
            self.__set_reverted()
        elif self.action == DatatableActionType.UPDATE.value:
            self.datatable.client.patch_row(self.old_row['_id'], self.old_row)
            self.__set_reverted()
        else:
            raise WrongAction(f'Action {self.action} is not proper action')

    def __set_reverted(self):
        """
        Sets reverted to True and push it to DB
        """
        self.reverted = True
        self.save(update_fields=['reverted'])

    class Meta:
        ordering = ['-created_at']

    # DRY Permissions

    @staticmethod
    def has_read_permission(request):
        return request.user.is_superuser or request.user.groups.filter(name__in=[settings.READONLY_GROUP_NAME,
                                                                                 settings.READWRITE_GROUP_NAME])

    @staticmethod
    def has_write_permission(request):
        return request.user.is_superuser or request.user.groups.filter(name=settings.READWRITE_GROUP_NAME)

    def has_object_write_permission(self, request):
        return self.has_write_permission(request)
