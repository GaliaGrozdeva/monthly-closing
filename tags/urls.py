from django.urls import path

from . import views

app_name = "tags"
urlpatterns = [
    path("", views.tag_list, name="list"),
    path("new/", views.tag_create, name="create"),
    path("<int:pk>/", views.tag_detail, name="detail"),
    path("<int:pk>/edit/", views.tag_edit, name="edit"),
    path("<int:pk>/delete/", views.tag_delete, name="delete"),
]
