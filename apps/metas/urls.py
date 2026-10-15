from django.urls import path

from . import views

app_name = "metas"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nova/", views.nova, name="nova"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
    path("<int:pk>/aporte/", views.aporte, name="aporte"),
    path("<int:pk>/aportes/<int:aporte_pk>/excluir/", views.aporte_excluir, name="aporte_excluir"),
]