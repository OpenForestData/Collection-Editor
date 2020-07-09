import json
from abc import ABC

import pymongo
from pymongo.cursor import Cursor
from rest_framework.settings import api_settings

from core.models.datatable import DatatableMongoClient
from core.utils import remove_prefix


class MongoFilter(ABC):
    def __init__(self, columns):
        self.columns = columns

    def get_valid_fields(self):
        return self.columns

    def remove_invalid_fields(self, fields):
        valid_fields = self.get_valid_fields()
        return [term for term in fields if term.lstrip('-') in valid_fields]


class RowOrdering(MongoFilter):
    ordering_param = api_settings.ORDERING_PARAM
    default_mongo_ordering = ('_id', pymongo.ASCENDING)

    def get_ordering(self, request):
        params = request.query_params.get(self.ordering_param)
        if params:
            fields = [param.strip() for param in params.split(',')]
            ordering = self.remove_invalid_fields(fields)
            if ordering:
                return [(field, pymongo.DESCENDING) if field.startswith('-') else (field, pymongo.ASCENDING)
                        for field in fields]

        # No ordering was included, or all the ordering fields were invalid
        return [self.default_mongo_ordering]

    def order_cursor(self, request, cursor: Cursor):
        ordering = self.get_ordering(request)

        if ordering:
            return cursor.sort(ordering)

        return cursor


class RowFiltering(MongoFilter):
    ordering_prefix = 'filter_'

    def get_filtering(self, request):
        params = {remove_prefix(param, self.ordering_prefix): val for param, val in request.query_params.items() if param.startswith(self.ordering_prefix)}
        filtering = None
        if params:
            valid_field_names = self.remove_invalid_fields(params)
            filtering = {key: self.columns[key](val) for key, val in params.items() if key in valid_field_names}
        return filtering

    def filter_cursor(self, request, client: DatatableMongoClient):
        filtering = self.get_filtering(request)

        if filtering:
            return client.get_rows(filtering)

        return client.get_rows()
