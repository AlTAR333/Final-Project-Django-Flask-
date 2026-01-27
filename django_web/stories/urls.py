from django.urls import path
from .views import home, api_test

urlpatterns = [
    path("", home),
    path("api-test/", api_test),
]
