from django.core.management.base import BaseCommand

from apps.pagar.services import gerar_contas


class Command(BaseCommand):
    help = "Gera as contas a pagar das recorrências ativas (pode rodar quantas vezes quiser)."

    def add_arguments(self, parser):
        parser.add_argument("--meses", type=int, default=3, help="Quantos meses à frente gerar.")

    def handle(self, *args, **opcoes):
        criadas = gerar_contas(opcoes["meses"])
        self.stdout.write(self.style.SUCCESS(f"{criadas} conta(s) a pagar criada(s)."))