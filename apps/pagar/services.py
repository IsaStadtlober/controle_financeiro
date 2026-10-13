import calendar
from datetime import date, timedelta

from .models import ContaPagar, Recorrencia


def _primeiro_dia(d, n):
    """Primeiro dia do mês que fica n meses depois de d."""
    m = d.month - 1 + n
    return date(d.year + m // 12, m % 12 + 1, 1)


def vencimentos(rec, ate):
    """Todas as datas de vencimento da recorrência, do início até `ate`."""
    limite = min(ate, rec.fim) if rec.fim else ate
    datas = []

    if rec.frequencia == Recorrencia.Frequencia.SEMANAL:
        d = rec.inicio
        while d <= limite:
            datas.append(d)
            d += timedelta(days=7)
        return datas

    passo = 12 if rec.frequencia == Recorrencia.Frequencia.ANUAL else 1
    base = rec.inicio.replace(day=1)
    n = 0
    while True:
        mes = _primeiro_dia(base, n * passo)
        ultimo = calendar.monthrange(mes.year, mes.month)[1]
        d = mes.replace(day=min(rec.dia_vencimento, ultimo))  # dia 31 vira 30 ou 28
        if d > limite:
            break
        if d >= rec.inicio:
            datas.append(d)
        n += 1
    return datas


def gerar_contas(meses=3):
    """Cria as contas a pagar das recorrências ativas para os próximos meses.
    Pode rodar quantas vezes quiser: não duplica. Devolve quantas foram criadas."""
    hoje = date.today()
    ate = _primeiro_dia(hoje.replace(day=1), meses + 1) - timedelta(days=1)
    criadas = 0

    for rec in Recorrencia.objects.filter(ativa=True):
        for venc in vencimentos(rec, ate):
            if venc < hoje.replace(day=1):
                continue  # não recria meses que já passaram
            _, criou = ContaPagar.objects.get_or_create(
                recorrencia=rec,
                vencimento=venc,
                defaults={
                    "descricao": rec.descricao,
                    "valor": rec.valor,
                    "categoria": rec.categoria,
                    "conta": rec.conta,
                },
            )
            criadas += criou
    return criadas