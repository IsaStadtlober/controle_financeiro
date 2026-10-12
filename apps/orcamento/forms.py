from django import forms

from apps.lancamentos.forms import CLASSE_CAMPO


class LimiteForm(forms.Form):
    limite = forms.DecimalField(
        label="Limite mensal (R$)",
        required=False,
        min_value=0,
        max_digits=14,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"step": "0.01", "placeholder": "0,00", "class": CLASSE_CAMPO}
        ),
    )