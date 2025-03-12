from django.urls import path
from .views import my_api_view


urlpatterns = [
    path("api/test/", my_api_view, name="my_api_view"),
]
