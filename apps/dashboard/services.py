"""Cálculos do dashboard. Tudo é agregado no banco a partir de Lancamento.

Regra central: transferências NUNCA entram em receitas nem em despesas.
"""
import calendar
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth

from apps.contas.models import Conta
from apps.contas.services import saldo_disponivel
from apps.lancamentos.models import Lancamento
from apps.orcamento.models import Orcamento
from apps.pagar.models import ContaPagar

ZERO = Decimal("0")

PERIODOS = {
    "mes_atual": "Mês atual",
    "mes_anterior": "Mês anterior",
    "3m": "Últimos 3 meses",
    "12m": "Últimos 12 meses",
}


def add_months(d, n):
    """Primeiro dia do mês que fica n meses depois (ou antes, se n < 0) de d."""
    m = d.month - 1 + n
    return date(d.year + m // 12, m % 12 + 1, 1)


def calcular_periodo(chave, hoje=None):
    """Devolve (ini, fim, ant_ini, ant_fim). O `fim` é exclusivo (não entra).

    O período anterior tem o mesmo número de dias, então um mês parcial
    (dia 1 a 11) é comparado com o mesmo trecho do mês passado (dia 1 a 11).
    """
    hoje = hoje or date.today()
    primeiro = hoje.replace(day=1)
    if chave == "mes_anterior":
        n = 1
        ini, fim = add_months(primeiro, -1), primeiro
    elif chave in ("3m", "12m"):
        n = 3 if chave == "3m" else 12
        ini, fim = add_months(primeiro, -(n - 1)), hoje + timedelta(days=1)
    else:  # mes_atual
        n = 1
        ini, fim = primeiro, hoje + timedelta(days=1)
    ant_ini = add_months(ini, -n)
    ant_fim = min(ant_ini + (fim - ini), ini)
    return ini, fim, ant_ini, ant_fim


def _base(conta_id=None):
    """Lançamentos que contam como receita/despesa (sem transferências)."""
    qs = Lancamento.objects.exclude(tipo=Lancamento.Tipo.TRANSFERENCIA)
    return qs.filter(conta_id=conta_id) if conta_id else qs


def totais(ini, fim, conta_id=None):
    r = _base(conta_id).filter(data__gte=ini, data__lt=fim).aggregate(
        receitas=Sum("valor", filter=Q(tipo=Lancamento.Tipo.RECEITA)),
        despesas=Sum("valor", filter=Q(tipo=Lancamento.Tipo.DESPESA)),
    )
    receitas, despesas = r["receitas"] or ZERO, r["despesas"] or ZERO
    return {"receitas": receitas, "despesas": despesas, "resultado": receitas - despesas}


def variacao(atual, anterior, mais_e_bom):
    """Variação % entre dois valores, com a classe visual: bom, ruim ou neutro."""
    if not anterior or atual == anterior:
        return {"pct": None if not anterior else Decimal("0"), "classe": "neutro", "sinal": ""}
    pct = (atual - anterior) / abs(anterior) * 100
    subiu = pct > 0
    return {
        "pct": pct,
        "classe": "bom" if subiu == mais_e_bom else "ruim",
        "sinal": "▲" if subiu else "▼",
    }


def saldo_do_card(conta_id=None):
    """Sem filtro: dinheiro disponível (corrente, poupança, carteira).
    Com filtro de conta: o saldo daquela conta, seja qual for o tipo."""
    if conta_id:
        conta = Conta.objects.filter(pk=conta_id, ativa=True).first()
        return conta.saldo if conta else ZERO
    return saldo_disponivel()


def cards(ini, fim, ant_ini, ant_fim, conta_id=None):
    atual = totais(ini, fim, conta_id)
    ant = totais(ant_ini, ant_fim, conta_id)
    return {
        "saldo": saldo_do_card(conta_id),
        "receitas": atual["receitas"],
        "despesas": atual["despesas"],
        "resultado": atual["resultado"],
        "var_receitas": variacao(atual["receitas"], ant["receitas"], True),
        "var_despesas": variacao(atual["despesas"], ant["despesas"], False),
        "var_resultado": variacao(atual["resultado"], ant["resultado"], True),
    }


def gastos_por_categoria(ini, fim, conta_id=None):
    qs = (
        _base(conta_id)
        .filter(tipo=Lancamento.Tipo.DESPESA, data__gte=ini, data__lt=fim)
        .values("categoria_id", "categoria__nome")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    return [
        {"id": r["categoria_id"], "nome": r["categoria__nome"], "total": float(r["total"])}
        for r in qs
    ]


def _acumulado_mes(primeiro, hoje, conta_id=None):
    """Gasto acumulado dia a dia no mês. Dias que ainda não chegaram ficam None."""
    ultimo = calendar.monthrange(primeiro.year, primeiro.month)[1]
    fim = primeiro.replace(day=ultimo) + timedelta(days=1)
    por_dia = {
        r["data"].day: r["t"]
        for r in _base(conta_id)
        .filter(tipo=Lancamento.Tipo.DESPESA, data__gte=primeiro, data__lt=fim)
        .values("data")
        .annotate(t=Sum("valor"))
    }
    acumulado, serie = ZERO, []
    for dia in range(1, ultimo + 1):
        if primeiro.replace(day=dia) > hoje:
            serie.append(None)
            continue
        acumulado += por_dia.get(dia, ZERO)
        serie.append(float(acumulado))
    return serie


def ritmo_de_gasto(hoje=None, conta_id=None):
    hoje = hoje or date.today()
    primeiro = hoje.replace(day=1)
    anterior = add_months(primeiro, -1)
    atual = _acumulado_mes(primeiro, hoje, conta_id)
    ant = _acumulado_mes(anterior, hoje, conta_id)
    dias = max(len(atual), len(ant))
    atual += [None] * (dias - len(atual))
    ant += [None] * (dias - len(ant))
    return {
        "dias": list(range(1, dias + 1)),
        "atual": atual,
        "anterior": ant,
        "rotulo_atual": f"Mês atual ({primeiro:%m/%Y})",
        "rotulo_anterior": f"Mês anterior ({anterior:%m/%Y})",
    }


def evolucao_mensal(hoje=None, conta_id=None):
    hoje = hoje or date.today()
    inicio = add_months(hoje.replace(day=1), -11)
    qs = (
        _base(conta_id)
        .filter(data__gte=inicio)
        .annotate(mes=TruncMonth("data"))
        .values("mes")
        .annotate(
            receitas=Sum("valor", filter=Q(tipo=Lancamento.Tipo.RECEITA)),
            despesas=Sum("valor", filter=Q(tipo=Lancamento.Tipo.DESPESA)),
        )
    )
    dados = {}
    for r in qs:
        mes = r["mes"].date() if hasattr(r["mes"], "date") else r["mes"]
        dados[mes] = r

    rotulos, receitas, despesas, resultado = [], [], [], []
    for i in range(12):
        mes = add_months(inicio, i)
        r = dados.get(mes, {})
        rec, desp = r.get("receitas") or ZERO, r.get("despesas") or ZERO
        rotulos.append(f"{mes:%m/%y}")
        receitas.append(float(rec))
        despesas.append(float(desp))
        resultado.append(float(rec - desp))
    return {"rotulos": rotulos, "receitas": receitas, "despesas": despesas, "resultado": resultado}


def orcamento_vs_realizado(mes):
    """Limite do orçamento x gasto realizado no mês (considera todas as contas)."""
    mes = mes.replace(day=1)
    fim = add_months(mes, 1)
    gasto = {
        r["categoria_id"]: r["t"]
        for r in Lancamento.objects.filter(
            tipo=Lancamento.Tipo.DESPESA, data__gte=mes, data__lt=fim
        )
        .values("categoria_id")
        .annotate(t=Sum("valor"))
    }
    itens = []
    for o in Orcamento.objects.filter(mes=mes).select_related("categoria"):
        realizado = gasto.get(o.categoria_id, ZERO)
        pct = float(realizado / o.limite * 100) if o.limite else 0.0
        itens.append(
            {
                "nome": o.categoria.nome,
                "limite": o.limite,
                "realizado": realizado,
                "pct": pct,
                "pct_barra": min(pct, 100),
                "nivel": "estourado" if pct > 100 else "alerta" if pct >= 80 else "ok",
            }
        )
    return sorted(itens, key=lambda i: i["pct"], reverse=True)


def maiores_despesas(ini, fim, conta_id=None, n=5):
    return list(
        _base(conta_id)
        .filter(tipo=Lancamento.Tipo.DESPESA, data__gte=ini, data__lt=fim)
        .select_related("categoria")
        .order_by("-valor")[:n]
    )


def proximos_vencimentos(n=5):
    return list(
        ContaPagar.objects.filter(pago_em__isnull=True)
        .select_related("categoria")
        .order_by("vencimento")[:n]
    )