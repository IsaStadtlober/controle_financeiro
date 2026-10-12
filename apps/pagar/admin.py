from django.contrib import admin

from .models import ContaPagar, Recorrencia


@admin.register(Recorrencia)
class RecorrenciaAdmin(admin.ModelAdmin):
    list_display = ("descricao", "valor", "frequencia", "dia_vencimento", "ativa")
    list_filter = ("frequencia", "ativa")


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ("descricao", "valor", "vencimento", "pago_em", "recorrencia")
    list_filter = ("pago_em",)
    date_hierarchy = "vencimento"