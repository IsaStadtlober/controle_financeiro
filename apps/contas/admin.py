from django.contrib import admin

from .models import Conta, Investimento


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "saldo_inicial", "ativa")
    list_filter = ("tipo", "ativa")


@admin.register(Investimento)
class InvestimentoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "valor_aplicado", "valor_atual", "atualizado_em")
    list_filter = ("tipo",)