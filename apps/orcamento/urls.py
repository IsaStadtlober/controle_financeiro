from django.urls import path

from . import views

app_name = "orcamento"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("copiar/", views.copiar, name="copiar"),
    path("<int:categoria_id>/editar/", views.editar, name="editar"),
]