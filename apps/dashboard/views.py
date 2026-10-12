from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.contas.models import Conta

from . import services


@login_required
def dashboard(request):
    hoje = date.today()

    # Lê os filtros da URL (?periodo=3m&conta=2), com valores seguros por padrão.
    chave = request.GET.get("periodo", "mes_atual")
    if chave not in services.PERIODOS:
        chave = "mes_atual"
    conta_id = request.GET.get("conta")
    conta_id = int(conta_id) if conta_id and conta_id.isdigit() else None

    ini, fim, ant_ini, ant_fim = services.calcular_periodo(chave, hoje)
    ultimo_dia = fim - timedelta(days=1)

    categorias = services.gastos_por_categoria(ini, fim, conta_id)[:8]
    for c in categorias:  # endereço de "drill-down": abre os lançamentos da categoria
        c["url"] = (
            f"/lancamentos/?tipo=despesa&categoria={c['id']}"
            f"&de={ini.isoformat()}&ate={ultimo_dia.isoformat()}"
        )

    contexto = {
        "periodos": services.PERIODOS,
        "periodo": chave,
        "contas": Conta.objects.filter(ativa=True),
        "conta_id": conta_id,
        "periodo_rotulo": f"{ini:%d/%m/%Y} a {ultimo_dia:%d/%m/%Y}",
        "cards": services.cards(ini, fim, ant_ini, ant_fim, conta_id),
        "orcamento": services.orcamento_vs_realizado(ultimo_dia),
        "mes_orcamento": ultimo_dia,
        "maiores": services.maiores_despesas(ini, fim, conta_id),
        "vencimentos": services.proximos_vencimentos(),
        "altura_categorias": max(300, min(len(categorias) * 44 + 40, 460)),
        "graficos": {
            "categorias": categorias,
            "ritmo": services.ritmo_de_gasto(hoje, conta_id),
            "evolucao": services.evolucao_mensal(hoje, conta_id),
        },
    }
    return render(request, "dashboard/index.html", contexto)