from django.core.management.base import BaseCommand

from apps.contas.patrimonio import registrar_snapshot


class Command(BaseCommand):
    help = "Grava a foto mensal do patrimônio (rode uma vez por mês; repetir só atualiza o mês)."

    def handle(self, *args, **opcoes):
        registro, criado = registrar_snapshot()
        acao = "criado" if criado else "atualizado"
        self.stdout.write(self.style.SUCCESS(f"Registro de {registro.mes:%m/%Y} {acao}: total {registro.total}."))