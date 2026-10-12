from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Categoria(models.Model):
    class Tipo(models.TextChoices):
        RECEITA = "receita", "Receita"
        DESPESA = "despesa", "Despesa"

    nome = models.CharField(max_length=80)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    categoria_pai = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="filhas"
    )
    icone = models.CharField(
        "ícone", max_length=40, blank=True, help_text="Classe do Font Awesome. Ex.: fa-house"
    )

    class Meta:
        ordering = ["tipo", "nome"]
        constraints = [
            models.UniqueConstraint(fields=["nome", "tipo"], name="uq_categoria_nome_tipo")
        ]

    def __str__(self):
        return self.nome


class Lancamento(models.Model):
    class Tipo(models.TextChoices):
        RECEITA = "receita", "Receita"
        DESPESA = "despesa", "Despesa"
        TRANSFERENCIA = "transferencia", "Transferência"

    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    valor = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    data = models.DateField(default=date.today)
    descricao = models.CharField(max_length=255, blank=True)
    conta = models.ForeignKey("contas.Conta", on_delete=models.PROTECT, related_name="lancamentos")
    conta_destino = models.ForeignKey(
        "contas.Conta",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="transferencias_recebidas",
    )
    categoria = models.ForeignKey(Categoria, null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-data", "-id"]
        indexes = [
            models.Index(fields=["data"], name="idx_lanc_data"),
            models.Index(fields=["categoria", "data"], name="idx_lanc_cat_data"),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(valor__gt=0), name="ck_lanc_valor_positivo")
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.valor} em {self.data:%d/%m/%Y}"

    def clean(self):
        erros = {}
        if self.tipo == self.Tipo.TRANSFERENCIA:
            if not self.conta_destino_id:
                erros["conta_destino"] = "Informe a conta de destino."
            elif self.conta_destino_id == self.conta_id:
                erros["conta_destino"] = "A conta de destino deve ser diferente da de origem."
            if self.categoria_id:
                erros["categoria"] = "Transferências não têm categoria."
        else:
            if not self.categoria_id:
                erros["categoria"] = "Informe a categoria."
            elif self.categoria.tipo != self.tipo:
                erros["categoria"] = "A categoria não corresponde ao tipo do lançamento."
            if self.conta_destino_id:
                erros["conta_destino"] = "Conta de destino só vale para transferências."
        if erros:
            raise ValidationError(erros)