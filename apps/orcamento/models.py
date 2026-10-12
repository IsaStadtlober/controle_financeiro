from django.db import models


class Orcamento(models.Model):
    categoria = models.ForeignKey("lancamentos.Categoria", on_delete=models.CASCADE)
    mes = models.DateField(help_text="Sempre o dia 1 do mês.")
    limite = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ["-mes", "categoria__nome"]
        constraints = [
            models.UniqueConstraint(fields=["categoria", "mes"], name="uq_orc_cat_mes")
        ]

    def save(self, *args, **kwargs):
        self.mes = self.mes.replace(day=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.categoria} - {self.mes:%m/%Y}"