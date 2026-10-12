from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.dashboard.services import add_months
from apps.lancamentos.models import Categoria

from . import services
from .forms import LimiteForm
from .models import Orcamento


def _mes_da_url(request):
    """Lê ?mes=2026-10 (GET ou POST). Se faltar ou for inválido, usa o mês atual."""
    texto = request.GET.get("mes") or request.POST.get("mes") or ""
    try:
        ano, mes = texto.split("-")
        return date(int(ano), int(mes), 1)
    except ValueError:
        return date.today().replace(day=1)


def _voltar_para(mes):
    return redirect(f"{reverse('orcamento:lista')}?mes={mes:%Y-%m}")


@login_required
def lista(request):
    mes = _mes_da_url(request)
    itens = services.resumo_do_mes(mes)
    return render(
        request,
        "orcamento/lista.html",
        {
            "mes": mes,
            "mes_anterior": f"{add_months(mes, -1):%Y-%m}",
            "mes_seguinte": f"{add_months(mes, 1):%Y-%m}",
            "mes_param": f"{mes:%Y-%m}",
            "itens": itens,
            "totais": services.totais_do_mes(itens),
        },
    )


@login_required
def editar(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id, tipo=Categoria.Tipo.DESPESA)
    mes = _mes_da_url(request)
    atual = Orcamento.objects.filter(categoria=categoria, mes=mes).first()
    form = LimiteForm(request.POST or None, initial={"limite": atual.limite if atual else None})

    if request.method == "POST" and form.is_valid():
        limite = form.cleaned_data["limite"]
        if limite:
            Orcamento.objects.update_or_create(
                categoria=categoria, mes=mes, defaults={"limite": limite}
            )
            messages.success(request, f"Limite de {categoria.nome} salvo.")
        else:  # campo vazio ou zero = remover o limite
            if atual:
                atual.delete()
            messages.success(request, f"Limite de {categoria.nome} removido.")
        return _voltar_para(mes)

    return render(
        request, "orcamento/form.html", {"categoria": categoria, "mes": mes, "mes_param": f"{mes:%Y-%m}"}
    )


@login_required
@require_POST
def copiar(request):
    mes = _mes_da_url(request)
    criados = services.copiar_do_mes_anterior(mes)
    if criados:
        messages.success(request, f"{criados} limite(s) copiado(s) do mês anterior.")
    else:
        messages.error(request, "Nada para copiar: o mês anterior não tem limites novos.")
    return _voltar_para(mes)