from django.contrib import admin

from .models import Categoria, Lancamento


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "icone", "categoria_pai")
    list_filter = ("tipo",)


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ("data", "tipo", "descricao", "categoria", "conta", "valor")
    list_filter = ("tipo", "conta", "categoria")
    date_hierarchy = "data"
    search_fields = ("descricao",)