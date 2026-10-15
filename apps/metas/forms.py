from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from apps.lancamentos.forms import FORMATOS_DATA, estilizar

from .models import Meta


def _widget_data():
    return forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class MetaForm(forms.ModelForm):
    class Meta:
        model = Meta
        fields = ["nome", "valor_alvo", "prazo"]
        widgets = {"prazo": _widget_data()}
        labels = {"valor_alvo": "Valor alvo (R$)", "prazo": "Prazo (opcional)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["prazo"].input_formats = FORMATOS_DATA
        self.fields["valor_alvo"].widget.attrs["placeholder"] = "0,00"
        estilizar(self)

    def clean_valor_alvo(self):
        valor = self.cleaned_data["valor_alvo"]
        if valor <= 0:
            raise ValidationError("O valor alvo deve ser maior que zero.")
        return valor


class AporteForm(forms.Form):
    operacao = forms.ChoiceField(
        label="Operação", choices=[("aporte", "Aporte (guardar)"), ("resgate", "Resgate (retirar)")]
    )
    valor = forms.DecimalField(
        label="Valor (R$)", min_value=0.01, max_digits=14, decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.01", "placeholder": "0,00"}),
    )
    data = forms.DateField(label="Data", input_formats=FORMATOS_DATA, widget=_widget_data())

    def __init__(self, *args, meta, **kwargs):
        super().__init__(*args, **kwargs)
        self.meta = meta
        self.fields["data"].initial = date.today()
        estilizar(self)

    def clean(self):
        cleaned = super().clean()
        valor, operacao = cleaned.get("valor"), cleaned.get("operacao")
        if valor and operacao == "resgate" and valor > self.meta.reservado:
            self.add_error("valor", f"Você só tem R$ {self.meta.reservado:.2f} reservados nesta meta.")
        return cleaned

    def valor_com_sinal(self):
        """Resgate é guardado como valor negativo."""
        valor = self.cleaned_data["valor"]
        return -valor if self.cleaned_data["operacao"] == "resgate" else valor