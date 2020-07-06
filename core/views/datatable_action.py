from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import DatatableAction
from core.serializers import DatatableActionReadOnlySerializer


class DatatableActionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DatatableAction.objects.all()
    serializer_class = DatatableActionReadOnlySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['datatable', 'action']

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
