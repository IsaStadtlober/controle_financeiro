from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import services
from .forms import AporteForm, MetaForm
from .models import Aporte, Meta


@login_required
def lista(request):
    itens = services.metas_com_resumo()
    return render(request, "metas/lista.html", {"itens": itens, "totais": services.totais(itens)})


@login_required
def detalhe(request, pk):
    meta = get_object_or_404(Meta, pk=pk)
    return render(
        request,
        "metas/detalhe.html",
        {"i": services.resumo_da_meta(meta), "aportes": meta.aportes.all()},
    )


@login_required
def nova(request):
    form = MetaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        meta = form.save()
        messages.success(request, f"Meta “{meta.nome}” criada. Faça o primeiro aporte!")
        return redirect("metas:lista")
    return render(request, "metas/form.html", {
        "form": form, "titulo": "Nova meta", "voltar": reverse("metas:lista")})


@login_required
def editar(request, pk):
    meta = get_object_or_404(Meta, pk=pk)
    form = MetaForm(request.POST or None, instance=meta)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Meta atualizada.")
        return redirect("metas:detalhe", pk=meta.pk)
    return render(request, "metas/form.html", {
        "form": form, "titulo": "Editar meta", "voltar": reverse("metas:detalhe", args=[meta.pk])})


@login_required
def excluir(request, pk):
    meta = get_object_or_404(Meta, pk=pk)
    if request.method == "POST":
        meta.delete()  # os aportes saem junto (on_delete=CASCADE)
        messages.success(request, "Meta excluída.")
        return redirect("metas:lista")
    return render(request, "metas/excluir.html", {"meta": meta, "qtd_aportes": meta.aportes.count()})


@login_required
def aporte(request, pk):
    meta = get_object_or_404(Meta, pk=pk)
    form = AporteForm(request.POST or None, meta=meta, initial={"operacao": request.GET.get("operacao", "aporte")})
    if request.method == "POST" and form.is_valid():
        Aporte.objects.create(meta=meta, valor=form.valor_com_sinal(), data=form.cleaned_data["data"])
        messages.success(request, "Movimentação registrada. O saldo das suas contas não mudou.")
        return redirect("metas:lista")
    return render(request, "metas/aporte.html", {"form": form, "i": services.resumo_da_meta(meta)})


@login_required
@require_POST
def aporte_excluir(request, pk, aporte_pk):
    meta = get_object_or_404(Meta, pk=pk)
    registro = get_object_or_404(Aporte, pk=aporte_pk, meta=meta)
    if meta.reservado - registro.valor < 0:
        messages.error(request, "Não dá para remover: o valor reservado ficaria negativo (há resgates depois dele).")
    else:
        registro.delete()
        messages.success(request, "Movimentação removida.")
    return redirect("metas:detalhe", pk=meta.pk)