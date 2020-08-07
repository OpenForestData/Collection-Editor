from dry_rest_permissions.generics import DRYPermissions
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.filters import RowOrdering, RowFiltering
from core.mixins import MultiSerializerMixin
from core.models import Datatable
from core.paginators import MongoCursorLimitOffsetPagination
from core.serializers import DatatableSerializer, DatatableReadOnlySerializer, DatatableRowsReadOnlySerializer, \
    DatatableRowsSerializer, DatatableExportSerializer


class DatatableViewSet(MultiSerializerMixin,
                       mixins.CreateModelMixin,
                       viewsets.ReadOnlyModelViewSet):
    permission_classes = (DRYPermissions,)
    serializers = {
        'default': DatatableReadOnlySerializer,
        'create': DatatableSerializer,
        'retrieve': DatatableRowsReadOnlySerializer,
        'add_row': DatatableRowsSerializer,
        'patch_row': DatatableRowsSerializer,
        'delete_row': DatatableRowsSerializer,
        'export': DatatableExportSerializer,
    }
    queryset = Datatable.objects.all()

    def retrieve(self, request, pk=None, **kwargs):
        """
        Retrieves rows of selected datatable, and list of columns for this datatable

        .. http:get:: /datatable/(int:datatable_id)/

            :query $column_name: value of specified column
                    eg.: ``?species=deer``
            :query logical_query: nested query build with ``and, or`` operators
                    eg.: ``?logical_query=or(species=deer, and(species=bear, color=black))``
            :query ordering: coma separated **$column_name** values, prefixed with '-' to sort descending
                    eg.: ``?ordering=species,-height``
            :query offset: offset number. default is 0
            :query limit: limit number. default is 100
            :reqheader Authorization: optional Bearer (JWT) token to authenticate
            :statuscode 200: no error
            :statuscode 401: user unauthorized
            :statuscode 403: user lacks permissions for this action
            :statuscode 404: there's no specified datatable

        """
        pagination_class = MongoCursorLimitOffsetPagination()
        instance = self.get_object()

        row_filter = RowFiltering(instance.columns)
        mongo_cursor = row_filter.filter_cursor(request, instance.client)

        ordering_filter = RowOrdering(instance.columns)
        mongo_cursor = ordering_filter.order_cursor(request, mongo_cursor)

        page = pagination_class.paginate_queryset(mongo_cursor, request)

        serializer = self.get_serializer(page, many=True)
        response = pagination_class.get_paginated_response(serializer.data)
        response.data['columns'] = instance.columns

        return response

    @action(detail=True, methods=['POST'], url_path='row', url_name='add-row')
    def add_row(self, request, pk=None, **kwargs):
        """
        Adds row to selected datatable

        .. http:post:: /datatable/(int:datatable_id)/row/

            :param $column_name: value of specified column
            :reqheader Authorization: optional Bearer (JWT) token to authenticate
            :statuscode 201: row added
            :statuscode 400: new row has to have at least one of existing columns
            :statuscode 401: user unauthorized
            :statuscode 403: user lacks permissions for this action
            :statuscode 404: there's no specified datatable

        """

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.add_row()

        mongo_cursor = instance.client.get_rows()

        pagination_class = MongoCursorLimitOffsetPagination()
        page = pagination_class.paginate_queryset(mongo_cursor, request)

        serializer = DatatableRowsReadOnlySerializer(page, many=True)
        return pagination_class.get_paginated_response(serializer.data)

    @action(detail=True, methods=['PATCH'], url_path='row/(?P<row_id>[^/.]+)', url_name='row')
    def patch_row(self, request, pk=None, row_id=None, **kwargs):
        """
        Patch row in selected datatable

        .. http:post:: /datatable/(int:datatable_id)/row/(row_id)/

            :param $column_name: value of specified column
            :reqheader Authorization: optional Bearer (JWT) token to authenticate
            :statuscode 201: row updated
            :statuscode 400: updated row has to have at least one of existing columns
            :statuscode 401: user unauthorized
            :statuscode 403: user lacks permissions for this action
            :statuscode 404: there's no specified row
            :statuscode 404: there's no specified datatable

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

        .. http:delete:: /datatable/(int:datatable_id)/row/(row_id)/

            :reqheader Authorization: optional Bearer (JWT) token to authenticate
            :statuscode 204: row deleted
            :statuscode 400: updated row has to have at least one of existing columns
            :statuscode 401: user unauthorized
            :statuscode 403: user lacks permissions for this action
            :statuscode 404: there's no specified row
            :statuscode 404: there's no specified datatable

        """
        instance = self.get_object()
        if not instance.client.has_row(row_id):
            return Response(data={'row_id': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        serializer.delete_row(row_id)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'])
    def export(self, request, pk=None, **kwargs):
        """
        Exports filtered (or not) Datatable to Dataverse as tabular datafile

        .. http:post:: /datatable/(int:datatable_id)/export/

            :query $column_name: value of specified column
                    eg.: ``?species=deer``
            :query logical_query: nested query build with ``and, or`` operators
                    eg.: ``?logical_query=or(species=deer, and(species=bear, color=black))``
            :query ordering: coma separated **$column_name** values, prefixed with '-' to sort descending
                    eg.: ``?ordering=species,-height``
            :param dataset_id: pid of Dataverse dataset
            :reqheader Accept: the response content type depends on
                              :mailheader:`Accept` header
            :reqheader Authorization: optional OAuth token to authenticate
            :resheader Content-Type: this depends on :mailheader:`Accept`
                                    header of request
            :statuscode 200: no error
            :statuscode 400: there's no connection to Dataverse
            :statuscode 400: there's no Dataset in Dataverse
            :statuscode 401: user unauthorized
            :statuscode 403: user lacks permissions for this action
            :statuscode 404: there's no user

        """
        instance = self.get_object()

        row_filter = RowFiltering(instance.columns)
        mongo_cursor = row_filter.filter_cursor(request, instance.client)

        ordering_filter = RowOrdering(instance.columns)
        mongo_cursor = ordering_filter.order_cursor(request, mongo_cursor)

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        export_response = serializer.export(mongo_cursor)
        return Response(export_response['content'],
                        status=status.HTTP_200_OK if export_response['status'] == 200
                        else status.HTTP_400_BAD_REQUEST)
