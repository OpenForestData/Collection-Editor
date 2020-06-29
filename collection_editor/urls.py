from django.contrib import admin
from django.urls import path
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
]
