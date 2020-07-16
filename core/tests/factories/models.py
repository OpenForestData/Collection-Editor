from datetime import datetime

import factory
from django.contrib.auth import get_user_model

from core.models import Datatable, DatatableAction


class DatatableFactory(factory.DjangoModelFactory):
    class Meta:
        model = Datatable

    title = factory.Faker('word')
    collection_name = factory.Sequence(lambda n: f'datatable_{n}')
    columns = {
        str(col_type.__name__).capitalize(): col_type for
        col_type in [str, int, float, complex, bool]
    }


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f'user_{n}')


class DatatableActionFactory(factory.DjangoModelFactory):
    class Meta:
        model = DatatableAction

    user = factory.SubFactory(UserFactory)
    action = 'CREATE'
    datatable = factory.SubFactory(DatatableFactory)

    created_at = datetime.now()

    old_row = {'_id': 'old_row_id'}
    new_row = {'_id': 'new_row_id'}
    reverted = False
