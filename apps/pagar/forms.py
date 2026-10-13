from django import forms
from django.core.exceptions import ValidationError

from apps.contas.models import Conta
from apps.lancamentos.forms import FORMATOS_DATA, estilizar
from apps.lancamentos.models import Categoria

from .models import ContaPagar, Recorrencia


def _widget_data():
    return forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class ContaPagarForm(forms.ModelForm):
    class Meta:
        model = ContaPagar
        fields = ["descricao", "valor", "vencimento", "categoria", "conta"]
        widgets = {"vencimento": _widget_data()}
        labels = {"descricao": "Descrição", "conta": "Conta de pagamento (opcional)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vencimento"].input_formats = FORMATOS_DATA
        self.fields["categoria"].queryset = Categoria.objects.filter(tipo="despesa")
        self.fields["conta"].queryset = Conta.objects.filter(ativa=True)
        self.fields["valor"].widget.attrs["placeholder"] = "0,00"
        estilizar(self)

    def clean_valor(self):
        valor = self.cleaned_data["valor"]
        if valor <= 0:
            raise ValidationError("O valor deve ser maior que zero.")
        return valor


class PagamentoForm(forms.Form):
    conta = forms.ModelChoiceField(queryset=Conta.objects.filter(ativa=True), label="Pago com a conta")
    data = forms.DateField(
        label="Data do pagamento", input_formats=FORMATOS_DATA, widget=_widget_data()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)


class RecorrenciaForm(forms.ModelForm):
    dia_vencimento = forms.IntegerField(
        label="Dia do vencimento",
        min_value=1,
        max_value=31,
        help_text="Em meses mais curtos, vence no último dia. Na frequência semanal, vale a data de início.",
    )

    class Meta:
        model = Recorrencia
        fields = ["descricao", "valor", "categoria", "conta", "frequencia",
                  "dia_vencimento", "inicio", "fim", "ativa"]
        widgets = {"inicio": _widget_data(), "fim": _widget_data()}
        labels = {"descricao": "Descrição", "conta": "Conta usada no pagamento",
                  "inicio": "Início", "fim": "Fim (opcional)", "ativa": "Recorrência ativa"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["inicio"].input_formats = FORMATOS_DATA
        self.fields["fim"].input_formats = FORMATOS_DATA
        self.fields["categoria"].queryset = Categoria.objects.filter(tipo="despesa")
        self.fields["conta"].queryset = Conta.objects.filter(ativa=True)
        estilizar(self)
        self.fields["ativa"].widget.attrs["class"] = "h-4 w-4 rounded border-slate-300 accent-green-600"

    def clean(self):
        cleaned = super().clean()
        inicio, fim = cleaned.get("inicio"), cleaned.get("fim")
        if inicio and fim and fim < inicio:
            self.add_error("fim", "O fim não pode ser antes do início.")
        valor = cleaned.get("valor")
        if valor is not None and valor <= 0:
            self.add_error("valor", "O valor deve ser maior que zero.")
        return cleaned