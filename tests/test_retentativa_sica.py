import unittest
from unittest.mock import Mock, patch
import requests
from sistema_pedido import cliente_site as site


class RetentativaSicaTests(unittest.TestCase):
    def test_ticket_anterior_e_confirmacao(self):
        for mensagem in ('Gerado anteriormente', 'Ticket já foi pedido', 'Ticket já gerado'):
            with self.subTest(mensagem=mensagem):
                html = '<div class="alert alert-danger alert-dismissable fade in">' + mensagem + '</div>'
                self.assertEqual(site.interpretar_resposta_pedido(html), (True, mensagem))

    def test_erro_real_nao_vira_confirmacao(self):
        for mensagem in ('Prontuário inválido', 'Ticket não foi gerado anteriormente'):
            html = '<div class="alert alert-danger alert-dismissable fade in">' + mensagem + '</div>'
            self.assertEqual(site.interpretar_resposta_pedido(html), (False, mensagem))

    def test_timeout_permite_tentar_de_novo(self):
        sessao = Mock()
        sucesso = Mock(text='<div class="alert alert-danger alert-dismissable fade in">Gerado anteriormente</div>')
        sessao.post.side_effect = [requests.Timeout('tempo esgotado'), sucesso]
        with patch.object(site, 'obter_token_csrf', return_value='teste'):
            self.assertFalse(site.realizar_pedido(sessao, 'teste')[0])
            self.assertTrue(site.realizar_pedido(sessao, 'teste')[0])
        self.assertEqual(sessao.post.call_count, 2)

    def test_prazo_apos_token_continua_impedindo_post(self):
        sessao = Mock()
        conferir = Mock(side_effect=ValueError('PRAZO_PERDIDO: limite atingido'))
        with patch.object(site, 'obter_token_csrf', return_value='teste'):
            ok, mensagem = site.realizar_pedido(sessao, 'teste', antes_de_enviar=conferir)
        self.assertFalse(ok)
        self.assertIn('PRAZO_PERDIDO:', mensagem)
        sessao.post.assert_not_called()

    def test_pagina_sem_confirmacao_nao_e_sucesso(self):
        self.assertFalse(site.interpretar_resposta_pedido('<html>Manutenção</html>')[0])
