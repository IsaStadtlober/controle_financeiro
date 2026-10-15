from django.urls import path

from . import views

app_name = "patrimonio"

urlpatterns = [
    path("", views.index, name="index"),
    path("registrar/", views.registrar, name="registrar"),
    path("investimentos/novo/", views.investimento_novo, name="investimento_novo"),
    path("investimentos/<int:pk>/editar/", views.investimento_editar, name="investimento_editar"),
    path("investimentos/<int:pk>/excluir/", views.investimento_excluir, name="investimento_excluir"),
]