from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ScoreViewSet


router = DefaultRouter()
router.register("", ScoreViewSet, basename="score")

urlpatterns = [
    path("", include(router.urls)),
]
