from datetime import date
from decimal import Decimal
from math import ceil

from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

from .models import Meta

ZERO = Decimal("0")


def _resumir(meta, reservado, hoje):
    """Transforma uma meta (e quanto já foi reservado nela) em um dicionário pronto para a tela."""
    faltam = max(meta.valor_alvo - reservado, ZERO)
    concluida = reservado >= meta.valor_alvo
    pct = float(min(reservado / meta.valor_alvo * 100, 100)) if meta.valor_alvo else 0.0
    item = {
        "meta": meta,
        "reservado": reservado,
        "faltam": faltam,
        "pct": pct,
        "concluida": concluida,
        "atrasada": False,
        "meses": None,
        "sugestao_mensal": None,
    }
    if meta.prazo and not concluida:
        dias = (meta.prazo - hoje).days
        if dias < 0:
            item["atrasada"] = True
        else:
            meses = max(1, ceil(dias / 30))
            item["meses"] = meses
            item["sugestao_mensal"] = faltam / meses
    return item


def metas_com_resumo(hoje=None):
    """Todas as metas com o valor reservado calculado numa única consulta."""
    hoje = hoje or date.today()
    metas = Meta.objects.annotate(
        total_reservado=Coalesce(
            Sum("aportes__valor"), Value(ZERO), output_field=DecimalField(max_digits=14, decimal_places=2)
        )
    )
    itens = [_resumir(m, m.total_reservado, hoje) for m in metas]
    # Em andamento primeiro (prazo mais próximo no topo, sem prazo por último); concluídas no fim.
    itens.sort(key=lambda i: (i["concluida"], i["meta"].prazo is None, i["meta"].prazo or date.max, i["meta"].nome))
    return itens


def resumo_da_meta(meta, hoje=None):
    return _resumir(meta, meta.reservado, hoje or date.today())


def totais(itens):
    return {
        "reservado": sum((i["reservado"] for i in itens), ZERO),
        "alvo": sum((i["meta"].valor_alvo for i in itens), ZERO),
        "concluidas": sum(1 for i in itens if i["concluida"]),
        "total": len(itens),
    }