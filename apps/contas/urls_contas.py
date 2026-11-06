from django.urls import path

from . import views

app_name = "contas"

urlpatterns = [
    path("", views.contas, name="lista"),
    path("nova/", views.conta_nova, name="nova"),
    path("<int:pk>/editar/", views.conta_editar, name="editar"),
    path("<int:pk>/excluir/", views.conta_excluir, name="excluir"),
]