import re

from django import forms
from django.core.exceptions import ValidationError

from apps.contas.models import Conta

from .models import Categoria, Lancamento, proxima_cor

# <input type="date"> envia a data em ISO (aaaa-mm-dd); o locale pt-br esperaria dd/mm/aaaa.
FORMATOS_DATA = ["%Y-%m-%d", "%d/%m/%Y"]

# Mesmo estilo dos campos do protótipo.
CLASSE_CAMPO = (
    "w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 "
    "rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
)


def estilizar(form):
    """Aplica a classe CSS a todos os campos do formulário."""
    for campo in form.fields.values():
        campo.widget.attrs["class"] = CLASSE_CAMPO


class LancamentoForm(forms.ModelForm):
    class Meta:
        model = Lancamento
        fields = ["tipo", "valor", "data", "descricao", "conta", "conta_destino", "categoria"]
        widgets = {"data": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data"].input_formats = FORMATOS_DATA
        self.fields["conta"].queryset = Conta.objects.filter(ativa=True)
        self.fields["conta_destino"].queryset = Conta.objects.filter(ativa=True)
        self.fields["conta"].label = "Conta"
        self.fields["conta_destino"].label = "Conta de destino"
        self.fields["valor"].widget.attrs["placeholder"] = "0,00"
        self.fields["descricao"].widget.attrs["placeholder"] = "Ex: Supermercado Extra"
        estilizar(self)

    def clean(self):
        cleaned = super().clean()
        # Campos que não se aplicam ao tipo escolhido são descartados.
        if cleaned.get("tipo") == Lancamento.Tipo.TRANSFERENCIA:
            cleaned["categoria"] = None
        elif cleaned.get("tipo"):
            cleaned["conta_destino"] = None
        return cleaned


class FiltroLancamentos(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Buscar por descrição ou categoria..."}),
    )
    tipo = forms.ChoiceField(required=False, choices=[("", "Todos os tipos")] + Lancamento.Tipo.choices)
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(), required=False, empty_label="Todas as categorias"
    )
    conta = forms.ModelChoiceField(
        queryset=Conta.objects.all(), required=False, empty_label="Todas as contas"
    )
    de = forms.DateField(
        required=False,
        input_formats=FORMATOS_DATA,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    ate = forms.DateField(
        required=False,
        input_formats=FORMATOS_DATA,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)
        self.fields["q"].widget.attrs["class"] += " pl-9"  # espaço para o ícone da lupa


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nome", "tipo", "icone", "cor"]
        widgets = {"cor": forms.TextInput(attrs={"type": "color"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nome"].widget.attrs["placeholder"] = "Ex: Pets"
        self.fields["icone"].widget.attrs["placeholder"] = "Ex: fa-paw"
        self.fields["icone"].help_text = "Nome do ícone do Font Awesome (fontawesome.com/icons). Pode deixar em branco."
        estilizar(self)
        self.fields["cor"].widget.attrs["class"] = (
            "h-10 w-20 p-1 rounded-xl border border-slate-200 dark:border-slate-700 bg-transparent cursor-pointer"
        )
        # O seletor já abre na cor da categoria; se for nova, numa cor que ainda não está em uso.
        self.initial["cor"] = self.instance.cor_exibicao if self.instance.pk else proxima_cor()

    def clean_icone(self):
        # Aceita "paw", "fa-paw" ou "fa-solid fa-paw" e guarda sempre no formato "fa-paw".
        valor = self.cleaned_data.get("icone", "").strip()
        if not valor:
            return ""
        nome = valor.split()[-1]
        return nome if nome.startswith("fa-") else f"fa-{nome}"

    def clean_cor(self):
        cor = self.cleaned_data.get("cor", "").strip()
        if cor and not re.fullmatch(r"#[0-9a-fA-F]{6}", cor):
            raise ValidationError("Use uma cor no formato #RRGGBB.")
        return cor