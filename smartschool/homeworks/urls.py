from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HomeworkViewSet


router = DefaultRouter()
router.register("", HomeworkViewSet, basename="homework")

urlpatterns = [
    path("", include(router.urls)),
]
