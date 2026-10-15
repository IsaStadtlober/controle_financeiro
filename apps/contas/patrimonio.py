"""Cálculos do patrimônio.

Patrimônio = saldos de todas as contas ativas + valor atual dos investimentos cadastrados.
Os saldos continuam sendo calculados (nunca guardados); só o histórico mensal é gravado.
"""
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from apps.dashboard.services import add_months, totais

from .models import Conta, Investimento, PatrimonioHistorico
from .services import saldos

ZERO = Decimal("0")


def composicao():
    """Divide o patrimônio em três partes: disponível, reserva e investimentos."""
    contas = list(Conta.objects.filter(ativa=True))
    saldo_de = saldos(contas)

    disponivel = reserva = caixa_investimento = ZERO
    por_conta = []
    for conta in contas:
        saldo = saldo_de[conta.pk]
        por_conta.append({"conta": conta, "saldo": saldo})
        if conta.tipo == Conta.Tipo.RESERVA:
            reserva += saldo
        elif conta.tipo == Conta.Tipo.INVESTIMENTO:
            caixa_investimento += saldo
        else:  # corrente, poupança, carteira
            disponivel += saldo

    posicoes = Investimento.objects.aggregate(aplicado=Sum("valor_aplicado"), atual=Sum("valor_atual"))
    aplicado, atual = posicoes["aplicado"] or ZERO, posicoes["atual"] or ZERO
    investimentos = caixa_investimento + atual

    return {
        "por_conta": por_conta,
        "disponivel": disponivel,
        "reserva": reserva,
        "investimentos": investimentos,
        "caixa_investimento": caixa_investimento,
        "posicoes_aplicado": aplicado,
        "posicoes_atual": atual,
        "rentabilidade": (atual - aplicado) / aplicado * 100 if aplicado else None,
        "total": disponivel + reserva + investimentos,
    }


def cobertura_da_reserva(reserva, hoje=None, meses=3):
    """Quantos meses de despesas a reserva cobre (média dos últimos meses completos)."""
    hoje = hoje or date.today()
    fim = hoje.replace(day=1)
    media = totais(add_months(fim, -meses), fim)["despesas"] / meses
    return reserva / media if media else None


def registrar_snapshot(hoje=None):
    """Grava (ou atualiza) a foto do patrimônio do mês. Devolve (registro, foi_criado)."""
    hoje = hoje or date.today()
    c = composicao()
    return PatrimonioHistorico.objects.update_or_create(
        mes=hoje.replace(day=1),
        defaults={
            "disponivel": c["disponivel"],
            "reserva": c["reserva"],
            "investimentos": c["investimentos"],
            "total": c["total"],
        },
    )


def historico_para_grafico(limite=24):
    registros = list(PatrimonioHistorico.objects.order_by("-mes")[:limite])[::-1]
    return {
        "rotulos": [f"{r.mes:%m/%y}" for r in registros],
        "total": [float(r.total) for r in registros],
        "disponivel": [float(r.disponivel) for r in registros],
        "reserva": [float(r.reserva) for r in registros],
        "investimentos": [float(r.investimentos) for r in registros],
    }