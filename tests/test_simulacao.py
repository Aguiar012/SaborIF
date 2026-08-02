import unittest
from datetime import date
from unittest.mock import patch

from sistema_pedido import iniciar_pedidos
from sistema_pedido.refeicoes import JANTAR


class SimulacaoTests(unittest.TestCase):
    @patch("sistema_pedido.iniciar_pedidos.enviar_email")
    @patch("sistema_pedido.iniciar_pedidos.registrar_historico_pedido")
    @patch("sistema_pedido.iniciar_pedidos.realizar_pedido")
    @patch("sistema_pedido.iniciar_pedidos.buscar_cardapio_site")
    @patch("sistema_pedido.iniciar_pedidos.buscar_alunos_para_dia")
    @patch("sistema_pedido.iniciar_pedidos.data_alvo_pedido")
    @patch("sistema_pedido.iniciar_pedidos.garantir_estrutura_refeicoes")
    @patch("sistema_pedido.iniciar_pedidos.validar_configuracao")
    def test_simulacao_nao_envia_nem_registra_pedido(
        self,
        validar,
        garantir_estrutura,
        data_alvo,
        buscar_alunos,
        buscar_cardapio,
        realizar_pedido,
        registrar_historico,
        enviar_email,
    ):
        data_alvo.return_value = date(2026, 8, 3)
        buscar_alunos.return_value = [{"id": 10, "prontuario": "pt0000000"}]

        with (
            patch.object(iniciar_pedidos, "MODO_TESTE", True),
            patch.object(iniciar_pedidos, "PRONTUARIO_TESTE", "pt0000000"),
            patch.object(iniciar_pedidos, "SIMULAR_PEDIDO", True),
            patch.object(iniciar_pedidos, "REFEICAO_ATUAL", JANTAR),
        ):
            iniciar_pedidos.principal()

        validar.assert_called_once()
        garantir_estrutura.assert_called_once()
        buscar_alunos.assert_called_once_with(1, JANTAR, "pt0000000")
        buscar_cardapio.assert_not_called()
        realizar_pedido.assert_not_called()
        registrar_historico.assert_not_called()
        enviar_email.assert_not_called()


if __name__ == "__main__":
    unittest.main()
