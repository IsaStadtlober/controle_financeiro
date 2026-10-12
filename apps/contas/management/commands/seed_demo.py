import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.contas.models import Conta, Investimento
from apps.lancamentos.models import Categoria, Lancamento
from apps.metas.models import Aporte, Meta
from apps.orcamento.models import Orcamento
from apps.pagar.models import ContaPagar, Recorrencia

D = Decimal

# (categoria, limite mensal, faixa de valor de cada gasto, quantos gastos por mês)
DESPESAS = [
    ("Moradia", 2200, (2000, 2100), 1),
    ("Mercado & Supermercado", 1500, (60, 280), 6),
    ("Transporte & Combustível", 800, (15, 90), 8),
    ("Alimentação fora", 700, (25, 110), 6),
    ("Lazer & Viagens", 600, (40, 220), 3),
    ("Saúde & Farmácia", 400, (50, 200), 2),
    ("Assinaturas & Serviços", 250, (20, 60), 3),
]


def primeiro_dia_meses_atras(hoje, n):
    """Primeiro dia do mês que ficou n meses para trás."""
    m = hoje.month - 1 - n
    return date(hoje.year + m // 12, m % 12 + 1, 1)


class Command(BaseCommand):
    help = "Cria dados fictícios (12 meses) para testar o dashboard."

    def add_arguments(self, parser):
        parser.add_argument("--limpar", action="store_true", help="Apaga TODOS os dados antes.")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["limpar"]:
            for modelo in (ContaPagar, Recorrencia, Aporte, Meta, Orcamento,
                           Lancamento, Investimento, Categoria, Conta):
                modelo.objects.all().delete()
        elif Conta.objects.exists():
            self.stdout.write("Já existem dados. Use --limpar para apagar tudo e recriar.")
            return

        rnd = random.Random(42)  # semente fixa: os números são sempre os mesmos
        hoje = date.today()

        corrente = Conta.objects.create(nome="Conta Corrente", tipo="corrente", saldo_inicial=D("1500"))
        carteira = Conta.objects.create(nome="Carteira", tipo="carteira", saldo_inicial=D("200"))
        Conta.objects.create(nome="Poupança", tipo="poupanca", saldo_inicial=D("5000"))
        reserva = Conta.objects.create(nome="Reserva de Emergência", tipo="reserva", saldo_inicial=D("15000"))
        corretora = Conta.objects.create(nome="Corretora", tipo="investimento", saldo_inicial=D("0"))

        cat_salario = Categoria.objects.create(nome="Salário", tipo="receita")
        cat_extra = Categoria.objects.create(nome="Renda extra", tipo="receita")
        cats = {nome: Categoria.objects.create(nome=nome, tipo="despesa") for nome, *_ in DESPESAS}

        def dia(mes, n):
            """Dia n do mês, ou None se essa data ainda não chegou."""
            d = mes.replace(day=min(n, 28))
            return d if d <= hoje else None

        lancamentos = []
        for atras in range(11, -1, -1):
            mes = primeiro_dia_meses_atras(hoje, atras)

            if dia(mes, 5):
                lancamentos.append(Lancamento(tipo="receita", valor=D("8500"), data=dia(mes, 5),
                                              descricao="Salário", conta=corrente, categoria=cat_salario))
            if rnd.random() < 0.35 and dia(mes, 18):
                lancamentos.append(Lancamento(tipo="receita", valor=D(rnd.randint(300, 1200)), data=dia(mes, 18),
                                              descricao="Freela", conta=corrente, categoria=cat_extra))
            if dia(mes, 10):
                lancamentos.append(Lancamento(tipo="transferencia", valor=D("1500"), data=dia(mes, 10),
                                              descricao="Aporte na reserva", conta=corrente, conta_destino=reserva))
            if dia(mes, 12):
                lancamentos.append(Lancamento(tipo="transferencia", valor=D("1000"), data=dia(mes, 12),
                                              descricao="Aporte em investimentos", conta=corrente, conta_destino=corretora))

            for nome, _limite, (minimo, maximo), quantidade in DESPESAS:
                for k in range(quantidade):
                    d = dia(mes, 7 if nome == "Moradia" else rnd.randint(1, 28))
                    if not d:
                        continue
                    valor = D(rnd.randint(minimo * 100, maximo * 100)) / 100
                    gasta_na_carteira = nome in ("Lazer & Viagens", "Alimentação fora") and rnd.random() < 0.3
                    lancamentos.append(Lancamento(
                        tipo="despesa", valor=valor, data=d, descricao=f"{nome} {k + 1}",
                        conta=carteira if gasta_na_carteira else corrente, categoria=cats[nome]))

        Lancamento.objects.bulk_create(lancamentos)

        mes_atual = hoje.replace(day=1)
        for nome, limite, *_ in DESPESAS:
            Orcamento.objects.create(categoria=cats[nome], mes=mes_atual, limite=D(limite))

        inicio = mes_atual - timedelta(days=60)
        for descricao, valor, nome_cat, dia_venc in [
            ("Condomínio", "450", "Moradia", 12),
            ("Energia elétrica", "220", "Moradia", 15),
            ("Plano de saúde", "680", "Saúde & Farmácia", 18),
            ("Internet", "110", "Assinaturas & Serviços", 20),
        ]:
            Recorrencia.objects.create(
                descricao=descricao, valor=D(valor), categoria=cats[nome_cat], conta=corrente,
                frequencia="mensal", dia_vencimento=dia_venc, inicio=inicio)
        call_command("gerar_recorrencias", meses=2)

        for nome, alvo, prazo, aportes in [
            ("Viagem de férias", 8000, hoje + timedelta(days=240), [500, 500, 700, 600]),
            ("Notebook novo", 6000, hoje + timedelta(days=120), [800, 1200, 600]),
            ("Entrada do apartamento", 60000, hoje + timedelta(days=900), [2000, 2500, 2500]),
        ]:
            meta = Meta.objects.create(nome=nome, valor_alvo=D(alvo), prazo=prazo)
            for n, valor in enumerate(aportes):
                Aporte.objects.create(meta=meta, valor=D(valor), data=hoje - timedelta(days=30 * (len(aportes) - n)))

        for nome, tipo, aplicado, atual in [
            ("Tesouro Selic 2029", "renda_fixa", 9000, 9780),
            ("CDB 110% CDI", "renda_fixa", 6000, 6450),
            ("ETF IVVB11", "acoes", 3000, 3390),
            ("FII HGLG11", "fiis", 2500, 2610),
        ]:
            Investimento.objects.create(nome=nome, tipo=tipo, conta=corretora,
                                        valor_aplicado=D(aplicado), valor_atual=D(atual), atualizado_em=hoje)

        self.stdout.write(self.style.SUCCESS(f"Pronto: {len(lancamentos)} lançamentos criados."))