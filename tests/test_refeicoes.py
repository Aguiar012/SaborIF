import unittest
from unittest.mock import Mock, patch

from sistema_pedido.cliente_site import realizar_pedido
from sistema_pedido.refeicoes import ALMOCO, JANTAR, obter_refeicao


class ObterRefeicaoTests(unittest.TestCase):
    def test_almoco_aceita_nome_com_ou_sem_acento_e_codigo(self):
        self.assertEqual(obter_refeicao("almoco"), ALMOCO)
        self.assertEqual(obter_refeicao("almoço"), ALMOCO)
        self.assertEqual(obter_refeicao(1), ALMOCO)

    def test_jantar_aceita_nome_apelido_e_codigo(self):
        self.assertEqual(obter_refeicao("jantar"), JANTAR)
        self.assertEqual(obter_refeicao("janta"), JANTAR)
        self.assertEqual(obter_refeicao(2), JANTAR)

    def test_valor_desconhecido_e_rejeitado(self):
        with self.assertRaisesRegex(ValueError, "Refeicao invalida"):
            obter_refeicao("cafe")


class RealizarPedidoTests(unittest.TestCase):
    @patch("sistema_pedido.cliente_site.interpretar_resposta_pedido")
    @patch("sistema_pedido.cliente_site.obter_token_csrf")
    def test_envia_tipo_dois_ao_pedir_jantar(self, obter_token, interpretar):
        obter_token.return_value = "token-de-teste"
        interpretar.return_value = (True, "Ticket gerado")

        resposta = Mock(text="resposta simulada")
        sessao = Mock()
        sessao.post.return_value = resposta

        sucesso, _ = realizar_pedido(sessao, "pt0000000", "jantar")

        self.assertTrue(sucesso)
        dados_enviados = sessao.post.call_args.kwargs["data"]
        self.assertEqual(dados_enviados["tipo"], "2")
        self.assertEqual(dados_enviados["prontuario"], "pt0000000")

    @patch("sistema_pedido.cliente_site.interpretar_resposta_pedido")
    @patch("sistema_pedido.cliente_site.obter_token_csrf")
    def test_almoco_continua_sendo_o_padrao(self, obter_token, interpretar):
        obter_token.return_value = "token-de-teste"
        interpretar.return_value = (True, "Ticket gerado")

        sessao = Mock()
        sessao.post.return_value = Mock(text="resposta simulada")

        realizar_pedido(sessao, "pt0000000")

        dados_enviados = sessao.post.call_args.kwargs["data"]
        self.assertEqual(dados_enviados["tipo"], "1")


if __name__ == "__main__":
    unittest.main()
