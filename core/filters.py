import re
from abc import ABC
from typing import Dict, List, Tuple

import pymongo
from pymongo.cursor import Cursor
from rest_framework.request import Request
from rest_framework.settings import api_settings

from core.models.datatable import DatatableMongoClient


class MongoFilter(ABC):
    """
    Abstract base class for filters operating on MongoDB cursor
    """
    def __init__(self, columns):
        self.columns = columns

    def get_valid_fields(self) -> Dict[str, type]:
        """
        Return Datatable columns as valid fields for filtering

        :return: dict of Datatable columns and their types
        """
        return self.columns

    def remove_invalid_fields(self, fields: list) -> list:
        """
        Removes invalid field from request query params

        :param fields: fields to be validated
        :return: list of valid fields
        """
        valid_fields = self.get_valid_fields()
        return [term for term in fields if term.lstrip('-') in valid_fields]

    def validate_fields(self, field_dict: dict) -> Dict[str, object]:
        """
        Removes invalid fields form given dict and cast type of valid ones to one specified by their column

        :param field_dict: fields to be validated
        :return: validated fields
        """
        valid_field_names = self.remove_invalid_fields(field_dict)
        return {key: self.columns[key](val) for key, val in field_dict.items() if
                key in valid_field_names}


class RowOrdering(MongoFilter):
    """
    Filter allowing ordering MongoDB cursor
    """
    ordering_param = api_settings.ORDERING_PARAM
    default_mongo_ordering = ('_id', pymongo.ASCENDING)

    def get_ordering(self, request: Request) -> List[Tuple[str, int]]:
        """
        Extracts rows ordering from request query params.
        If no ordering params are found in request, orders by default from ``self.default_mongo_ordering``.

        :param request: request with ordering params
        :return: list of tuples `(column name, asc or desc order in Mongo notation)`
        """
        params = request.query_params.get(self.ordering_param)
        if params:
            fields = [param.strip() for param in params.split(',')]
            ordering = self.remove_invalid_fields(fields)
            if ordering:
                return [(field[1:], pymongo.DESCENDING) if field.startswith('-') else (field, pymongo.ASCENDING)
                        for field in fields]

        # No ordering was included, or all the ordering fields were invalid
        return [self.default_mongo_ordering]

    def order_cursor(self, request: Request, cursor: Cursor) -> Cursor:
        """
        Orders cursor based on request ordering params

        :param request: Request to extract ordering params from
        :param cursor: Cursor to be ordered
        :return: Ordered cursor
        """
        ordering = self.get_ordering(request)
        return cursor.sort(ordering)


class RowFiltering(MongoFilter):
    """
    Filter allowing both simple and logical filtering MongoDB cursor
    """
    logical_param = 'logical_query'
    supported_logical_operation = ['or', 'and']

    def get_filtering(self, request) -> Dict[str, object]:
        """
        Extracts filtering params from request

        :param request: Request to extract filtering params from
        :return: Dict representing MongoDB compliant query
        """
        filtering_params = {param: val for param, val in
                            request.query_params.items()}
        filtering = None
        if filtering_params:
            filtering = self.validate_fields(filtering_params)
        return filtering

    def get_logical_query(self, request) -> dict:
        """
        Extracts logical query from request

        :param request: Request to extract logical query from
        :return: Dict representing MongoDB compliant query
        """

        logical_param: str = request.query_params.get(self.logical_param)
        if logical_param:
            return self.__build_logical_queries(logical_param)

    def __build_logical_queries(self, query_param: str) -> dict:
        """
        Builds logical query dict form query param string.

        :param query_param: should look like: 'operation(field=value, field=value, operation(field=value, ...))'
        :return: logical query as a dict that has MongoDB query structure
        """

        # check if query_params is a logical query
        logical_query = self.__find_logical_queries(query_param)
        if not logical_query:
            # if it's not a query there should be coma separated parameters
            return self.__get_logical_query_params(query_param)

        for operator, params in logical_query.items():
            logical_query[operator] = []
            # strip params from brackets '()' and regex split on comas ',' not in brackets '()'
            for param in re.split(r',(?=[^)]*(?:\(|$))', params[1:-1]):
                logical_params = self.__build_logical_queries(param.strip())
                if logical_params:
                    logical_query[operator].append(logical_params)
        return {operator: query for operator, query in logical_query.items() if query}

    def __find_logical_queries(self, string: str) -> dict:
        """
        Finds logical query in given string. As regex is greedy it finds only the outer operation, and treat
        rest of a string as parameters.

        :param string: string to be check for logical query eg.: ``or(species=deer, and(species=bear, color=black))``
        :return: dict where key in an logical operator preceded by $ and value is parameters of the operation
        """
        operations = '|'.join(self.supported_logical_operation)
        results = re.findall(r'(' + operations + r')(\(.*\))', string)
        return {f'${result[0]}': result[1] for result in results}

    def __get_logical_query_params(self, string: str) -> dict:
        """
        Finds parameters that are in 'Field=Value' format

        :param string: string to be check for parameters
        :return: validated dict of fields
        """
        # matches pairs of strings connected with '='
        results = re.findall(r'(.*?)=(.*)', string)
        result = {result[0]: result[1] for result in results}
        return self.validate_fields(result)

    def filter_cursor(self, request: Request, client: DatatableMongoClient) -> Cursor:
        """
        Creates filtered cursor based on request filtering params

        :param request: Request to extract logical query from
        :param client: MongoDB client to be used for cursor creation
        :return: filtered cursor
        """

        logical_filtering = self.get_logical_query(request)
        if logical_filtering:
            return client.get_rows(logical_filtering)

        filtering = self.get_filtering(request)
        if filtering:
            return client.get_rows(filtering)

        return client.get_rows()
