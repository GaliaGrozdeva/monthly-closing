from django.urls import path

from . import views

app_name = "procedures"
urlpatterns = [
    path("", views.procedure_list, name="list"),
    path("new/", views.procedure_create, name="create"),
    path("<int:pk>/", views.procedure_detail, name="detail"),
    path("<int:pk>/edit/", views.procedure_edit, name="edit"),
    path("<int:pk>/delete/", views.procedure_delete, name="delete"),
]
