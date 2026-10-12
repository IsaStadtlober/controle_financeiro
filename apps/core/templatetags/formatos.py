from decimal import Decimal

from django import template

register = template.Library()


def formatar_brl(valor):
    valor = Decimal(valor or 0)
    sinal = "-" if valor < 0 else ""
    inteiro, frac = f"{abs(valor):,.2f}".split(".")
    return f"{sinal}R$ {inteiro.replace(',', '.')},{frac}"


@register.filter
def brl(valor):
    return formatar_brl(valor)