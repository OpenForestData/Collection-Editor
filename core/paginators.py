from pymongo.cursor import Cursor
from rest_framework.pagination import LimitOffsetPagination


class MongoCursorLimitOffsetPagination(LimitOffsetPagination):
    """
    Paginator for MongoDB Cursor build on DRF pagination
    """
    max_limit = 1000

    def paginate_queryset(self, cursor: Cursor, request, view=None):
        self.count = self.get_count(cursor)
        self.limit = self.get_limit(request)
        self.offset = self.get_offset(request)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []
        return list(cursor.skip(self.offset).limit(self.limit))

    def get_count(self, cursor: Cursor):
        return cursor.count()
