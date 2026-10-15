from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("lancamentos/", include("apps.lancamentos.urls")),
    path("orcamento/", include("apps.orcamento.urls")),
    path("pagar/", include("apps.pagar.urls")),
    path("patrimonio/", include("apps.contas.urls")),
    path("metas/", include("apps.metas.urls")),
    path("", include("apps.dashboard.urls")),
]