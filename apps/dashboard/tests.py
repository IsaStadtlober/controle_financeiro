from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.contas.models import Conta
from apps.contas.services import saldo_disponivel, saldos
from apps.dashboard import services
from apps.lancamentos.models import Categoria, Lancamento
from apps.pagar.models import ContaPagar

D = Decimal


class RegrasFinanceirasTest(TestCase):
    def setUp(self):
        # Roda antes de CADA teste, num banco de teste vazio.
        self.corrente = Conta.objects.create(nome="Corrente", tipo="corrente", saldo_inicial=D("1000"))
        self.reserva = Conta.objects.create(nome="Reserva", tipo="reserva", saldo_inicial=D("5000"))
        self.sal = Categoria.objects.create(nome="Salário", tipo="receita")
        self.mer = Categoria.objects.create(nome="Mercado", tipo="despesa")
        criar = Lancamento.objects.create
        criar(tipo="receita", valor=D("3000"), data=date(2026, 10, 5), conta=self.corrente, categoria=self.sal)
        criar(tipo="despesa", valor=D("400"), data=date(2026, 10, 6), conta=self.corrente, categoria=self.mer)
        criar(tipo="transferencia", valor=D("500"), data=date(2026, 10, 7),
              conta=self.corrente, conta_destino=self.reserva)

    def test_saldo_e_calculado_com_transferencias(self):
        s = saldos()
        self.assertEqual(s[self.corrente.pk], D("1000") + D("3000") - D("400") - D("500"))
        self.assertEqual(s[self.reserva.pk], D("5500"))

    def test_saldo_disponivel_ignora_reserva(self):
        self.assertEqual(saldo_disponivel(), D("3100"))

    def test_transferencia_nao_entra_em_receitas_nem_despesas(self):
        t = services.totais(date(2026, 10, 1), date(2026, 11, 1))
        self.assertEqual(t["receitas"], D("3000"))
        self.assertEqual(t["despesas"], D("400"))
        self.assertEqual(t["resultado"], D("2600"))

    def test_variacao_neutra_e_classes(self):
        self.assertEqual(services.variacao(D("100"), D("100"), True)["classe"], "neutro")
        self.assertEqual(services.variacao(D("150"), D("100"), True)["classe"], "bom")
        self.assertEqual(services.variacao(D("150"), D("100"), False)["classe"], "ruim")
        self.assertIsNone(services.variacao(D("10"), D("0"), True)["pct"])

    def test_periodo_parcial_compara_mesmo_intervalo(self):
        ini, fim, ant_ini, ant_fim = services.calcular_periodo("mes_atual", date(2026, 10, 10))
        self.assertEqual((ini, fim), (date(2026, 10, 1), date(2026, 10, 11)))
        self.assertEqual((ant_ini, ant_fim), (date(2026, 9, 1), date(2026, 9, 11)))

    def test_evolucao_bate_com_lancamentos(self):
        ev = services.evolucao_mensal(date(2026, 10, 10))
        self.assertEqual(ev["rotulos"][-1], "10/26")
        self.assertEqual(ev["receitas"][-1], 3000.0)
        self.assertEqual(ev["despesas"][-1], 400.0)

    def test_validacao_de_lancamento(self):
        categoria_errada = Lancamento(tipo="despesa", valor=D("10"), data=date.today(),
                                      conta=self.corrente, categoria=self.sal)
        with self.assertRaises(ValidationError):
            categoria_errada.full_clean()
        mesma_conta = Lancamento(tipo="transferencia", valor=D("10"), data=date.today(),
                                 conta=self.corrente, conta_destino=self.corrente)
        with self.assertRaises(ValidationError):
            mesma_conta.full_clean()

    def test_pagar_conta_gera_lancamento(self):
        cp = ContaPagar.objects.create(descricao="Luz", valor=D("200"), vencimento=date(2026, 10, 15),
                                       categoria=self.mer, conta=self.corrente)
        cp.pagar(data=date(2026, 10, 14))
        cp.refresh_from_db()
        self.assertEqual(cp.status, "paga")
        self.assertEqual(cp.lancamento.valor, D("200"))
        self.assertEqual(saldos()[self.corrente.pk], D("1000") + D("3000") - D("400") - D("500") - D("200"))


class ViewsTest(TestCase):
    def setUp(self):
        get_user_model().objects.create_user("eu", password="senha-forte-123")

    def test_exige_login(self):
        resposta = self.client.get(reverse("dashboard"))
        self.assertEqual(resposta.status_code, 302)  # 302 = redirecionou para o login

    def test_telas_renderizam_e_formulario_salva(self):
        self.client.login(username="eu", password="senha-forte-123")
        conta = Conta.objects.create(nome="Corrente", tipo="corrente")
        cat = Categoria.objects.create(nome="Mercado", tipo="despesa")
        Lancamento.objects.create(tipo="despesa", valor=D("50"), data=date.today(), conta=conta, categoria=cat)

        for periodo in ("mes_atual", "mes_anterior", "3m", "12m"):
            self.assertEqual(self.client.get(reverse("dashboard"), {"periodo": periodo}).status_code, 200)
        self.assertEqual(self.client.get(reverse("lancamentos:lista"),
                                         {"tipo": "despesa", "categoria": cat.pk}).status_code, 200)

        resposta = self.client.post(reverse("lancamentos:novo"), {
            "tipo": "despesa", "valor": "12.50", "data": date.today().isoformat(),
            "conta": conta.pk, "categoria": cat.pk, "descricao": "teste",
        })
        self.assertEqual(resposta.status_code, 302)  # salvou e redirecionou
        self.assertEqual(Lancamento.objects.count(), 2)