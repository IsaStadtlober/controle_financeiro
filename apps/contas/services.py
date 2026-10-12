from decimal import Decimal

from django.db.models import Sum

from .models import Conta


def saldos(contas=None):
    """Saldo de cada conta, calculado (nunca armazenado):
    saldo_inicial + receitas - despesas - transferências enviadas + transferências recebidas.

    Retorna {conta_id: Decimal}. Usa 2 consultas, independente do nº de contas.
    """
    from apps.lancamentos.models import Lancamento

    contas = list(Conta.objects.all() if contas is None else contas)
    resultado = {c.pk: c.saldo_inicial for c in contas}
    ids = list(resultado)

    saidas = (
        Lancamento.objects.filter(conta_id__in=ids)
        .values("conta_id", "tipo")
        .annotate(total=Sum("valor"))
    )
    for linha in saidas:
        if linha["tipo"] == Lancamento.Tipo.RECEITA:
            resultado[linha["conta_id"]] += linha["total"]
        else:  # despesa e transferência enviada saem da conta
            resultado[linha["conta_id"]] -= linha["total"]

    entradas = (
        Lancamento.objects.filter(tipo=Lancamento.Tipo.TRANSFERENCIA, conta_destino_id__in=ids)
        .values("conta_destino_id")
        .annotate(total=Sum("valor"))
    )
    for linha in entradas:
        resultado[linha["conta_destino_id"]] += linha["total"]

    return resultado


def saldo_disponivel(conta_id=None):
    """Dinheiro disponível: só corrente, poupança e carteira (ativas)."""
    contas = Conta.objects.filter(ativa=True, tipo__in=Conta.TIPOS_DISPONIVEIS)
    if conta_id:
        contas = contas.filter(pk=conta_id)
    return sum(saldos(contas).values(), Decimal("0"))