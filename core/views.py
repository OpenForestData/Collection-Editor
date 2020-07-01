from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.mixins import MultiSerializerMixin
from core.models import Datatable
from core.paginators import MongoCursorLimitOffsetPagination
from core.serializers import DatatableSerializer, DatatableReadSerializer, DatatableRowsSerializer


class DatatableViewSet(MultiSerializerMixin,
                       mixins.CreateModelMixin,
                       viewsets.ReadOnlyModelViewSet):
    serializers = {
        'default': DatatableReadSerializer,
        'create': DatatableSerializer,
        'retrieve': DatatableRowsSerializer
    }
    queryset = Datatable.objects.all()

    def retrieve(self, request, pk=None, **kwargs):
        pagination_class = MongoCursorLimitOffsetPagination()
        instance = self.get_object()
        mongo_cursor = instance.client.get_rows_cursor()

        page = pagination_class.paginate_queryset(mongo_cursor, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return pagination_class.get_paginated_response(serializer.data)

        serializer = self.get_serializer(mongo_cursor, many=True)
        return Response(serializer.data)
