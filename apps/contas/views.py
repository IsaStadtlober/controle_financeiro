from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.db.models import ProtectedError

from . import patrimonio
from .forms import ContaForm, InvestimentoForm
from .models import Conta, Investimento, PatrimonioHistorico
from .services import saldos


@login_required
def index(request):
    comp = patrimonio.composicao()
    return render(
        request,
        "patrimonio/index.html",
        {
            "comp": comp,
            "cobertura": patrimonio.cobertura_da_reserva(comp["reserva"]),
            "investimentos": Investimento.objects.select_related("conta"),
            "ultimo_registro": PatrimonioHistorico.objects.order_by("-mes").first(),
            "historico": patrimonio.historico_para_grafico(),
        },
    )


@login_required
@require_POST
def registrar(request):
    _, criado = patrimonio.registrar_snapshot()
    messages.success(
        request, "Patrimônio do mês registrado." if criado else "Registro do mês atualizado com os valores de hoje."
    )
    return redirect("patrimonio:index")


@login_required
def investimento_novo(request):
    form = InvestimentoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.atualizado_em = date.today()
        obj.save()
        messages.success(request, "Investimento salvo.")
        return redirect("patrimonio:index")
    return render(request, "patrimonio/form.html", {"form": form, "titulo": "Novo investimento"})


@login_required
def investimento_editar(request, pk):
    obj = get_object_or_404(Investimento, pk=pk)
    form = InvestimentoForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if {"valor_atual", "valor_aplicado"} & set(form.changed_data):
            obj.atualizado_em = date.today()  # valores mudaram: registra a data da atualização
        obj.save()
        messages.success(request, "Investimento atualizado.")
        return redirect("patrimonio:index")
    return render(request, "patrimonio/form.html", {"form": form, "titulo": "Editar investimento"})


@login_required
def investimento_excluir(request, pk):
    obj = get_object_or_404(Investimento, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Investimento excluído.")
        return redirect("patrimonio:index")
    return render(request, "patrimonio/excluir.html", {"obj": obj})

@login_required
def contas(request):
    lista = list(Conta.objects.all())  # todas, inclusive as inativas
    saldo_de = saldos(lista)
    for c in lista:
        c.saldo_atual = saldo_de[c.pk]
    return render(request, "contas/lista.html", {"contas": lista})


@login_required
def conta_nova(request):
    form = ContaForm(request.POST or None, initial={"ativa": True})
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Conta criada.")
        return redirect("contas:lista")
    return render(request, "contas/form.html", {"form": form, "titulo": "Nova conta"})


@login_required
def conta_editar(request, pk):
    obj = get_object_or_404(Conta, pk=pk)
    form = ContaForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Conta atualizada.")
        return redirect("contas:lista")
    return render(request, "contas/form.html", {"form": form, "titulo": "Editar conta"})


@login_required
def conta_excluir(request, pk):
    obj = get_object_or_404(Conta, pk=pk)
    if request.method == "POST":
        try:
            obj.delete()
            messages.success(request, "Conta excluída.")
        except ProtectedError:
            messages.error(
                request,
                f'Não dá para excluir "{obj.nome}": ela tem lançamentos ou contas a pagar. '
                "Edite a conta e desmarque “Conta ativa” para escondê-la sem perder o histórico.",
            )
        return redirect("contas:lista")
    return render(request, "contas/excluir.html", {"obj": obj})