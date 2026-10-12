from decimal import Decimal

from django.db.models import Sum

from apps.dashboard.services import add_months
from apps.lancamentos.models import Categoria, Lancamento

from .models import Orcamento

ZERO = Decimal("0")


def nivel_do_gasto(pct):
    if pct > 100:
        return "estourado"
    return "alerta" if pct >= 80 else "ok"


def resumo_do_mes(mes):
    """Uma linha por categoria de despesa: limite (se houver) x gasto realizado no mês."""
    mes = mes.replace(day=1)
    fim = add_months(mes, 1)

    gasto = {
        r["categoria_id"]: r["total"]
        for r in Lancamento.objects.filter(
            tipo=Lancamento.Tipo.DESPESA, data__gte=mes, data__lt=fim
        )
        .values("categoria_id")
        .annotate(total=Sum("valor"))
    }
    limites = {o.categoria_id: o.limite for o in Orcamento.objects.filter(mes=mes)}

    itens = []
    for cat in Categoria.objects.filter(tipo=Categoria.Tipo.DESPESA):
        limite = limites.get(cat.pk)
        item = {"categoria": cat, "limite": limite, "realizado": gasto.get(cat.pk, ZERO)}
        if limite:
            pct = float(item["realizado"] / limite * 100)
            item.update(
                restante=limite - item["realizado"],
                pct=pct,
                pct_barra=min(pct, 100),
                nivel=nivel_do_gasto(pct),
            )
        itens.append(item)

    # Com limite primeiro (os mais consumidos no topo); sem limite depois, por nome.
    itens.sort(key=lambda i: (i["limite"] is None, -i.get("pct", 0), i["categoria"].nome))
    return itens


def totais_do_mes(itens):
    com_limite = [i for i in itens if i["limite"]]
    return {
        "planejado": sum((i["limite"] for i in com_limite), ZERO),
        "realizado": sum((i["realizado"] for i in com_limite), ZERO),
        "sem_orcamento": sum((i["realizado"] for i in itens if not i["limite"]), ZERO),
    }


def copiar_do_mes_anterior(mes):
    """Copia os limites do mês anterior para as categorias que ainda não têm limite neste mês.
    Devolve quantos limites foram criados."""
    mes = mes.replace(day=1)
    ja_tem = set(Orcamento.objects.filter(mes=mes).values_list("categoria_id", flat=True))
    novos = [
        Orcamento(categoria_id=o.categoria_id, mes=mes, limite=o.limite)
        for o in Orcamento.objects.filter(mes=add_months(mes, -1))
        if o.categoria_id not in ja_tem
    ]
    Orcamento.objects.bulk_create(novos)
    return len(novos)