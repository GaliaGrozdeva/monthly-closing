from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("categories/", include("categories.urls")),
]
