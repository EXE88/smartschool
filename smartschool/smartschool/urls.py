from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class SuperuserSpectacularAPIView(SpectacularAPIView):
    permission_classes = (IsSuperUser,)


class SuperuserSpectacularSwaggerView(SpectacularSwaggerView):
    permission_classes = (IsSuperUser,)


class SuperuserSpectacularRedocView(SpectacularRedocView):
    permission_classes = (IsSuperUser,)


urlpatterns = [
    path(f'{settings.ADMIN_PATH}/', admin.site.urls),
    path('api/schema/', SuperuserSpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SuperuserSpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SuperuserSpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/accounts/', include('accounts.urls')),
    path('api/scores/', include('scores.urls')),
    path('api/homeworks/', include('homeworks.urls')),
    path('api/attendances/', include('attendances.urls')),
    path('api/comments/', include('comments.urls')),
]

