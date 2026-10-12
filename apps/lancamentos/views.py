from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import FiltroLancamentos, LancamentoForm
from .models import Categoria, Lancamento


@login_required
def lista(request):
    filtro = FiltroLancamentos(request.GET)
    qs = Lancamento.objects.select_related("categoria", "conta", "conta_destino")

    if filtro.is_valid():
        f = filtro.cleaned_data
        if f["q"]:
            qs = qs.filter(Q(descricao__icontains=f["q"]) | Q(categoria__nome__icontains=f["q"]))
        if f["tipo"]:
            qs = qs.filter(tipo=f["tipo"])
        if f["categoria"]:
            qs = qs.filter(categoria=f["categoria"])
        if f["conta"]:
            qs = qs.filter(Q(conta=f["conta"]) | Q(conta_destino=f["conta"]))
        if f["de"]:
            qs = qs.filter(data__gte=f["de"])
        if f["ate"]:
            qs = qs.filter(data__lte=f["ate"])

    soma = qs.exclude(tipo=Lancamento.Tipo.TRANSFERENCIA).aggregate(
        rec=Sum("valor", filter=Q(tipo="receita")),
        desp=Sum("valor", filter=Q(tipo="despesa")),
    )

    pagina = Paginator(qs, 25).get_page(request.GET.get("pagina"))
    params = request.GET.copy()
    params.pop("pagina", None)

    return render(
        request,
        "lancamentos/lista.html",
        {
            "filtro": filtro,
            "pagina": pagina,
            "soma": soma,
            "querystring": params.urlencode(),
        },
    )


def _categorias_json():
    return [{"id": c.pk, "nome": c.nome, "tipo": c.tipo} for c in Categoria.objects.all()]


@login_required
def novo(request):
    form = LancamentoForm(request.POST or None, initial={"tipo": request.GET.get("tipo", "despesa")})
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Lançamento salvo.")
        return redirect("lancamentos:lista")
    return render(
        request,
        "lancamentos/form.html",
        {"form": form, "titulo": "Novo lançamento", "categorias_json": _categorias_json()},
    )


@login_required
def editar(request, pk):
    obj = get_object_or_404(Lancamento, pk=pk)
    form = LancamentoForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Lançamento atualizado.")
        return redirect("lancamentos:lista")
    return render(
        request,
        "lancamentos/form.html",
        {"form": form, "titulo": "Editar lançamento", "categorias_json": _categorias_json()},
    )


@login_required
def excluir(request, pk):
    obj = get_object_or_404(Lancamento, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Lançamento excluído.")
        return redirect("lancamentos:lista")
    return render(request, "lancamentos/excluir.html", {"obj": obj})