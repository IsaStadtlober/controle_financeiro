from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import services
from .forms import ContaPagarForm, PagamentoForm, RecorrenciaForm
from .models import ContaPagar, Recorrencia

STATUS = {
    "abertas": "Em aberto",
    "atrasadas": "Atrasadas",
    "pagas": "Pagas",
    "todas": "Todas",
}


@login_required
def lista(request):
    hoje = date.today()
    status = request.GET.get("status", "abertas")
    if status not in STATUS:
        status = "abertas"

    qs = ContaPagar.objects.select_related("categoria", "conta")
    if status == "abertas":
        qs = qs.filter(pago_em__isnull=True).order_by("vencimento")
    elif status == "atrasadas":
        qs = qs.filter(pago_em__isnull=True, vencimento__lt=hoje).order_by("vencimento")
    elif status == "pagas":
        qs = qs.filter(pago_em__isnull=False).order_by("-pago_em")
    else:
        qs = qs.order_by("-vencimento")

    resumo = ContaPagar.objects.filter(pago_em__isnull=True).aggregate(
        aberto=Sum("valor"),
        atrasado=Sum("valor", filter=Q(vencimento__lt=hoje)),
        n_atrasadas=Count("pk", filter=Q(vencimento__lt=hoje)),
        semana=Sum("valor", filter=Q(vencimento__gte=hoje, vencimento__lte=hoje + timedelta(days=7))),
    )
    pagina = Paginator(qs, 25).get_page(request.GET.get("pagina"))
    return render(
        request,
        "pagar/lista.html",
        {"pagina": pagina, "status": status, "status_opcoes": STATUS, "resumo": resumo},
    )


def _bloqueia_se_paga(request, conta):
    """Contas já pagas não são alteradas: o pagamento gerou um lançamento."""
    if conta.pago_em:
        messages.error(request, "Essa conta já foi paga. Desfaça o pagamento para alterá-la.")
        return redirect("pagar:lista")
    return None


@login_required
def nova(request):
    form = ContaPagarForm(request.POST or None, initial={"vencimento": date.today()})
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Conta a pagar salva.")
        return redirect("pagar:lista")
    return render(request, "pagar/form.html", {
        "form": form, "titulo": "Nova conta a pagar", "voltar": "pagar:lista"})


@login_required
def editar(request, pk):
    conta = get_object_or_404(ContaPagar, pk=pk)
    if bloqueio := _bloqueia_se_paga(request, conta):
        return bloqueio
    form = ContaPagarForm(request.POST or None, instance=conta)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Conta a pagar atualizada.")
        return redirect("pagar:lista")
    return render(request, "pagar/form.html", {
        "form": form, "titulo": "Editar conta a pagar", "voltar": "pagar:lista"})


@login_required
def excluir(request, pk):
    conta = get_object_or_404(ContaPagar, pk=pk)
    if bloqueio := _bloqueia_se_paga(request, conta):
        return bloqueio
    if request.method == "POST":
        conta.delete()
        messages.success(request, "Conta a pagar excluída.")
        return redirect("pagar:lista")
    return render(request, "pagar/excluir.html", {"conta": conta})


@login_required
def pagar(request, pk):
    conta = get_object_or_404(ContaPagar, pk=pk)
    if bloqueio := _bloqueia_se_paga(request, conta):
        return bloqueio
    form = PagamentoForm(request.POST or None, initial={"conta": conta.conta_id, "data": date.today()})
    if request.method == "POST" and form.is_valid():
        conta.pagar(conta=form.cleaned_data["conta"], data=form.cleaned_data["data"])
        messages.success(request, f"“{conta.descricao}” paga. O lançamento foi criado.")
        return redirect("pagar:lista")
    return render(request, "pagar/pagar.html", {"form": form, "conta": conta})


@login_required
@require_POST
def desfazer(request, pk):
    conta = get_object_or_404(ContaPagar, pk=pk)
    conta.desfazer_pagamento()
    messages.success(request, f"Pagamento de “{conta.descricao}” desfeito. O lançamento foi removido.")
    return redirect("pagar:lista")


@login_required
def recorrencias(request):
    return render(request, "pagar/recorrencias.html", {
        "recorrencias": Recorrencia.objects.select_related("categoria", "conta")})


@login_required
def recorrencia_nova(request):
    form = RecorrenciaForm(request.POST or None, initial={"inicio": date.today(), "ativa": True})
    if request.method == "POST" and form.is_valid():
        form.save()
        services.gerar_contas()  # já cria as próximas contas, sem esperar o comando
        messages.success(request, "Recorrência salva e contas dos próximos meses geradas.")
        return redirect("pagar:recorrencias")
    return render(request, "pagar/form.html", {
        "form": form, "titulo": "Nova recorrência", "voltar": "pagar:recorrencias"})


@login_required
def recorrencia_editar(request, pk):
    rec = get_object_or_404(Recorrencia, pk=pk)
    form = RecorrenciaForm(request.POST or None, instance=rec)
    if request.method == "POST" and form.is_valid():
        form.save()
        services.gerar_contas()
        messages.success(request, "Recorrência atualizada. Contas já geradas não mudam.")
        return redirect("pagar:recorrencias")
    return render(request, "pagar/form.html", {
        "form": form, "titulo": "Editar recorrência", "voltar": "pagar:recorrencias"})


@login_required
@require_POST
def gerar(request):
    criadas = services.gerar_contas()
    if criadas:
        messages.success(request, f"{criadas} conta(s) a pagar criada(s).")
    else:
        messages.success(request, "Tudo em dia: não havia contas novas para gerar.")
    return redirect("pagar:recorrencias")