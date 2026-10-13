from django.urls import path

from . import views

app_name = "pagar"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nova/", views.nova, name="nova"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
    path("<int:pk>/pagar/", views.pagar, name="pagar"),
    path("<int:pk>/desfazer/", views.desfazer, name="desfazer"),
    path("recorrencias/", views.recorrencias, name="recorrencias"),
    path("recorrencias/nova/", views.recorrencia_nova, name="recorrencia_nova"),
    path("recorrencias/gerar/", views.gerar, name="gerar"),
    path("recorrencias/<int:pk>/editar/", views.recorrencia_editar, name="recorrencia_editar"),
]