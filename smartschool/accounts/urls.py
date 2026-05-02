from django.urls import path

from .views import AccountDashboardAPIView


urlpatterns = [
    path("me/", AccountDashboardAPIView.as_view(), name="account-dashboard"),
]

