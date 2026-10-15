from django.contrib import admin

from .models import Conta, Investimento, PatrimonioHistorico


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "saldo_inicial", "ativa")
    list_filter = ("tipo", "ativa")


@admin.register(Investimento)
class InvestimentoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "valor_aplicado", "valor_atual", "atualizado_em")
    list_filter = ("tipo",)

@admin.register(PatrimonioHistorico)
class PatrimonioHistoricoAdmin(admin.ModelAdmin):
    list_display = ("mes", "disponivel", "reserva", "investimentos", "total")