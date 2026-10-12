from datetime import date

from django.db import models, transaction


class Recorrencia(models.Model):
    class Frequencia(models.TextChoices):
        MENSAL = "mensal", "Mensal"
        ANUAL = "anual", "Anual"
        SEMANAL = "semanal", "Semanal"

    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    categoria = models.ForeignKey("lancamentos.Categoria", on_delete=models.PROTECT)
    conta = models.ForeignKey("contas.Conta", on_delete=models.PROTECT)
    frequencia = models.CharField(
        max_length=10, choices=Frequencia.choices, default=Frequencia.MENSAL
    )
    dia_vencimento = models.PositiveSmallIntegerField(help_text="Dia do mês (1 a 31).")
    inicio = models.DateField()
    fim = models.DateField(null=True, blank=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "recorrência"
        verbose_name_plural = "recorrências"
        ordering = ["descricao"]

    def __str__(self):
        return self.descricao


class ContaPagar(models.Model):
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    vencimento = models.DateField()
    categoria = models.ForeignKey("lancamentos.Categoria", on_delete=models.PROTECT)
    conta = models.ForeignKey("contas.Conta", null=True, blank=True, on_delete=models.PROTECT)
    recorrencia = models.ForeignKey(
        Recorrencia, null=True, blank=True, on_delete=models.SET_NULL, related_name="contas"
    )
    lancamento = models.OneToOneField(
        "lancamentos.Lancamento", null=True, blank=True, on_delete=models.SET_NULL
    )
    pago_em = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "conta a pagar"
        verbose_name_plural = "contas a pagar"
        ordering = ["vencimento"]
        indexes = [models.Index(fields=["vencimento"], name="idx_pagar_venc")]
        constraints = [
            models.UniqueConstraint(
                fields=["recorrencia", "vencimento"], name="uq_pagar_recorrencia_venc"
            )
        ]

    def __str__(self):
        return f"{self.descricao} ({self.vencimento:%d/%m/%Y})"

    @property
    def status(self):
        if self.pago_em:
            return "paga"
        return "atrasada" if self.vencimento < date.today() else "a_vencer"

    @transaction.atomic
    def pagar(self, conta=None, data=None):
        """Marca como paga e cria o lançamento de despesa correspondente."""
        from apps.lancamentos.models import Lancamento

        if self.pago_em:
            return self.lancamento
        conta = conta or self.conta
        if conta is None:
            raise ValueError("Informe a conta usada no pagamento.")
        data = data or date.today()
        lanc = Lancamento.objects.create(
            tipo=Lancamento.Tipo.DESPESA,
            valor=self.valor,
            data=data,
            descricao=self.descricao,
            conta=conta,
            categoria=self.categoria,
        )
        self.conta, self.lancamento, self.pago_em = conta, lanc, data
        self.save(update_fields=["conta", "lancamento", "pago_em"])
        return lanc