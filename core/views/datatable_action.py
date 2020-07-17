from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import DatatableAction
from core.serializers import DatatableActionReadOnlySerializer


class DatatableActionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DatatableAction.objects.all()
    serializer_class = DatatableActionReadOnlySerializer
    permission_classes = (DRYPermissions,)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filter_fields = ['datatable', 'action', 'user', 'reverted']
    ordering_fields = ['created_at']

    @action(detail=True, methods=['POST'])
    def revert(self, request, pk=None, **kwargs):
        """
        Reverts Datatable action form history
        """
        instance: DatatableAction = self.get_object()
        if instance.reverted:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'non_field_errors': 'This history action has already been reverted.'})
        instance.revert_action()

        return Response(status=status.HTTP_200_OK)
