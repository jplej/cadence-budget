from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("htmx-test/", views.htmx_test, name="htmx-test"),
]
