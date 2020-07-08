from rest_framework import status, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.filters import RowOrdering
from core.mixins import MultiSerializerMixin
from core.models import Datatable
from core.paginators import MongoCursorLimitOffsetPagination
from core.serializers import DatatableSerializer, DatatableReadOnlySerializer, DatatableRowsReadOnlySerializer, \
    DatatableRowsSerializer


class DatatableViewSet(MultiSerializerMixin,
                       mixins.CreateModelMixin,
                       viewsets.ReadOnlyModelViewSet):
    serializers = {
        'default': DatatableReadOnlySerializer,
        'create': DatatableSerializer,
        'retrieve': DatatableRowsReadOnlySerializer,
        'add_row': DatatableRowsSerializer,
        'patch_row': DatatableRowsSerializer,
        'delete_row': DatatableRowsSerializer
    }
    queryset = Datatable.objects.all()

    def retrieve(self, request, pk=None, **kwargs):
        """
        Retrieve rows of selected datatable
        """
        pagination_class = MongoCursorLimitOffsetPagination()
        instance = self.get_object()
        mongo_cursor = instance.client.get_rows()

        ordering_filter = RowOrdering(instance.columns)
        mongo_cursor = ordering_filter.order_cursor(request, mongo_cursor)

        page = pagination_class.paginate_queryset(mongo_cursor, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return pagination_class.get_paginated_response(serializer.data)

        serializer = self.get_serializer(mongo_cursor, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], url_path='row', url_name='add-row')
    def add_row(self, request, pk=None, **kwargs):
        """
        Adds row to selected datatable
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.add_row()

        mongo_cursor = instance.client.get_rows()

        pagination_class = MongoCursorLimitOffsetPagination()
        page = pagination_class.paginate_queryset(mongo_cursor, request)
        if page is not None:
            serializer = DatatableRowsReadOnlySerializer(page, many=True)
            return pagination_class.get_paginated_response(serializer.data)

        serializer = DatatableRowsReadOnlySerializer(mongo_cursor, many=True)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['PATCH'], url_path='row/(?P<row_id>[^/.]+)', url_name='row')
    def patch_row(self, request, pk=None, row_id=None, **kwargs):
        """
        Patch row in selected datatable
        """
        instance = self.get_object()
        if not instance.client.has_row(row_id):
            return Response(data={'row_id': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.patch_row(row_id)

        return Response(status=status.HTTP_200_OK)

    @patch_row.mapping.delete
    def delete_row(self, request, pk=None, row_id=None, **kwargs):
        """
        Deletes row in selected datatable
        """
        instance = self.get_object()
        if not instance.client.has_row(row_id):
            return Response(data={'row_id': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        serializer.delete_row(row_id)

        return Response(status=status.HTTP_204_NO_CONTENT)
