from django.conf import settings
from django.test import TestCase

from core.tests.factories.models import UserFactory


class UtilsTestCase(TestCase):
    def test_user_default_group(self):
        user = UserFactory()
        self.assertTrue(user.groups.filter(name=settings.READONLY_GROUP_NAME))

        user.groups.clear()
        user.save()
        self.assertFalse(user.groups.filter(name=settings.READONLY_GROUP_NAME))
