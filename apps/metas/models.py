from decimal import Decimal

from django.db import models
from django.db.models import Sum


class Meta(models.Model):
    nome = models.CharField(max_length=100)
    valor_alvo = models.DecimalField(max_digits=14, decimal_places=2)
    prazo = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["prazo", "nome"]

    def __str__(self):
        return self.nome

    @property
    def reservado(self):
        # "Dinheiro carimbado": não movimenta nenhuma conta.
        return self.aportes.aggregate(t=Sum("valor"))["t"] or Decimal("0")

    @property
    def percentual(self):
        if not self.valor_alvo:
            return Decimal("0")
        return min(self.reservado / self.valor_alvo * 100, Decimal("100"))


class Aporte(models.Model):
    meta = models.ForeignKey(Meta, on_delete=models.CASCADE, related_name="aportes")
    valor = models.DecimalField(max_digits=14, decimal_places=2, help_text="Negativo = resgate.")
    data = models.DateField()

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"{self.meta}: {self.valor}"