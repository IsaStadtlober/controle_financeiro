from django import forms
from django.core.exceptions import ValidationError

from apps.lancamentos.forms import estilizar

from .models import Conta, Investimento


class InvestimentoForm(forms.ModelForm):
    class Meta:
        model = Investimento
        fields = ["nome", "tipo", "conta", "valor_aplicado", "valor_atual"]
        labels = {"conta": "Conta / corretora (opcional)", "valor_aplicado": "Valor aplicado (R$)",
                  "valor_atual": "Valor atual (R$)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["conta"].queryset = Conta.objects.filter(ativa=True)
        estilizar(self)

    def _nao_negativo(self, campo):
        valor = self.cleaned_data[campo]
        if valor < 0:
            raise ValidationError("O valor não pode ser negativo.")
        return valor

    def clean_valor_aplicado(self):
        return self._nao_negativo("valor_aplicado")

    def clean_valor_atual(self):
        return self._nao_negativo("valor_atual")

class ContaForm(forms.ModelForm):
    class Meta:
        model = Conta
        fields = ["nome", "tipo", "saldo_inicial", "ativa"]
        labels = {"saldo_inicial": "Saldo inicial (R$)", "ativa": "Conta ativa"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nome"].widget.attrs["placeholder"] = "Ex: Nubank"
        self.fields["saldo_inicial"].widget.attrs["placeholder"] = "0,00"
        self.fields["saldo_inicial"].help_text = (
            "Quanto a conta tinha ao começar a usar o sistema. "
            "O saldo atual = saldo inicial + lançamentos."
        )
        estilizar(self)
        # estilizar() põe a aparência de "caixa de texto" em tudo; o checkbox precisa de outra.
        self.fields["ativa"].widget.attrs["class"] = "h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"