from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.urls import urlpatterns as datatable_urls
from core.views.users import get_current_user

api_urlpatterns = [
    path('admin/', admin.site.urls),

    url(r'^datatable/', include(datatable_urls)),
    url(r'^user/me$', get_current_user, name='me'),

    # JWT Token
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns = [
    path('api/', include(api_urlpatterns))
]
