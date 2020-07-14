from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


from core.urls import urlpatterns as datatable_urls

urlpatterns = [
    path('admin/', admin.site.urls),

    url(r'^datatable/', include(datatable_urls)),

    # JWT Token
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
