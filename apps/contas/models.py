from decimal import Decimal

from django.db import models

class Conta(models.Model):
    class Tipo(models.TextChoices):
        CORRENTE = "corrente", "Conta corrente"
        POUPANCA = "poupanca", "Poupança"
        CARTEIRA = "carteira", "Carteira"
        RESERVA = "reserva", "Reserva de emergência"
        INVESTIMENTO = "investimento", "Investimento"

    # Tipos que contam como "dinheiro disponível" no dashboard.
    TIPOS_DISPONIVEIS = (Tipo.CORRENTE, Tipo.POUPANCA, Tipo.CARTEIRA)

    nome = models.CharField(max_length=80)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    saldo_inicial = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    @property
    def disponivel(self):
        return self.tipo in self.TIPOS_DISPONIVEIS

    @property
    def saldo(self):
        from .services import saldos

        return saldos([self])[self.pk]

class Investimento(models.Model):
    class Tipo(models.TextChoices):
        RENDA_FIXA = "renda_fixa", "Renda fixa"
        ACOES = "acoes", "Ações"
        FIIS = "fiis", "FIIs"
        CRIPTO = "cripto", "Cripto"
        OUTRO = "outro", "Outro"

    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    conta = models.ForeignKey(Conta, null=True, blank=True, on_delete=models.SET_NULL)
    valor_aplicado = models.DecimalField(max_digits=14, decimal_places=2)
    valor_atual = models.DecimalField(max_digits=14, decimal_places=2)
    atualizado_em = models.DateField()

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    @property
    def rentabilidade(self):
        if not self.valor_aplicado:
            return Decimal("0")
        return (self.valor_atual - self.valor_aplicado) / self.valor_aplicado * 100

class PatrimonioHistorico(models.Model):
    """Uma "foto" do patrimônio por mês, usada no gráfico de evolução."""

    mes = models.DateField(unique=True, help_text="Sempre o dia 1 do mês.")
    disponivel = models.DecimalField(max_digits=14, decimal_places=2)
    reserva = models.DecimalField(max_digits=14, decimal_places=2)
    investimentos = models.DecimalField(max_digits=14, decimal_places=2)
    total = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ["mes"]
        verbose_name = "registro de patrimônio"
        verbose_name_plural = "histórico do patrimônio"

    def __str__(self):
        return f"{self.mes:%m/%Y}: {self.total}"