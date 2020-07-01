from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include

from core.urls import urlpatterns as datatable_urls

urlpatterns = [
    path('admin/', admin.site.urls),

    url(r'^datatable', include(datatable_urls)),
]
