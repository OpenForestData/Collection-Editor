from django.conf.urls import url
from django.urls import include, path
from rest_framework import routers

from core import views

router = routers.DefaultRouter()
router.register('history', views.DatatableActionViewSet)
router.register('', views.DatatableViewSet)

urlpatterns = [
    url('', include(router.urls)),
]
