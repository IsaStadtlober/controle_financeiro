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