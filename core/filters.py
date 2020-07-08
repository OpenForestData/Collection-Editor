from abc import ABC

import pymongo
from pymongo.cursor import Cursor
from rest_framework.settings import api_settings


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
