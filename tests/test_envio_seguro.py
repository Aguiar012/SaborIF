import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from unittest.mock import Mock, patch
import requests
import psycopg
from sistema_pedido import envio_seguro as seguro
from sistema_pedido import cliente_site as site


class EnvioTests(unittest.TestCase):
    def enviar(self):
        return seguro.realizar_pedido_seguro(Mock(), 1, 'teste', date(2026, 10, 6),
                                           'almoco', date(2026, 10, 5))

    def test_reserva_ocupada_nao_envia(self):
        with patch.object(seguro, 'reservar', return_value=False), patch.object(seguro, 'realizar_pedido') as post:
            self.assertIn('ENVIO_RESERVADO', self.enviar()[1])
            post.assert_not_called()

    def test_resposta_incerta_preserva_reserva(self):
        with patch.object(seguro, 'reservar', return_value=True), patch.object(seguro, 'realizar_pedido', side_effect=site.PedidoIncerto()), patch.object(seguro, 'concluir') as concluir:
            self.assertIn('ENVIO_INCERTO', self.enviar()[1])
            self.assertEqual(concluir.call_args.args[3], 'incerto')

    def test_falha_antes_do_post_libera_para_reserva(self):
        with patch.object(seguro, 'reservar', return_value=True), patch.object(seguro, 'realizar_pedido', return_value=(False, 'CSRF indisponivel')), patch.object(seguro, 'concluir') as concluir:
            self.assertFalse(self.enviar()[0])
            self.assertEqual(concluir.call_args.args[3], 'nao_enviado')

    def test_sucesso_grava_confirmacao(self):
        with patch.object(seguro, 'reservar', return_value=True), patch.object(seguro, 'realizar_pedido', return_value=(True, 'Ticket gerado')), patch.object(seguro, 'concluir') as concluir:
            self.assertTrue(self.enviar()[0])
            self.assertEqual(concluir.call_args.args[3], 'confirmado')

    def test_timeout_post_e_incerto(self):
        sessao = Mock()
        sessao.post.side_effect = requests.Timeout()
        with patch.object(site, 'obter_token_csrf', return_value='teste'):
            with self.assertRaises(site.PedidoIncerto):
                site.realizar_pedido(sessao, 'teste')

    def test_html_sem_confirmacao_e_incerto(self):
        sessao = Mock()
        sessao.post.return_value = Mock(text='<html>manutencao</html>')
        with patch.object(site, 'obter_token_csrf', return_value='teste'):
            with self.assertRaises(site.PedidoIncerto):
                site.realizar_pedido(sessao, 'teste')

    def test_prazo_apos_token_nao_envia(self):
        sessao = Mock()
        with patch.object(site, 'obter_token_csrf', return_value='teste'):
            ok, mensagem = site.realizar_pedido(sessao, 'teste', antes_de_enviar=Mock(side_effect=ValueError('PRAZO_PERDIDO')))
            self.assertFalse(ok)
            self.assertIn('PRAZO_PERDIDO', mensagem)
            sessao.post.assert_not_called()


@unittest.skipUnless(os.getenv('TEST_DATABASE_URL'), 'Requer PostgreSQL isolado de testes')
class ConcorrenciaPostgresTests(unittest.TestCase):
    def setUp(self):
        # Exclusivamente banco descartável, nunca DATABASE_URL de produção.
        self.url = os.environ['TEST_DATABASE_URL']
        with psycopg.connect(self.url) as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS aluno (id bigint PRIMARY KEY)')
            conn.execute('CREATE TABLE IF NOT EXISTS pedido (aluno_id bigint,dia_pedido date,refeicao text,motivo text)')
            conn.execute('INSERT INTO aluno VALUES (1) ON CONFLICT DO NOTHING')
        self.patcher = patch.object(seguro, 'URL_BANCO_DADOS', self.url)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        seguro.preparar_reservas()
        with psycopg.connect(self.url) as conn:
            conn.execute('TRUNCATE envio_pedido, pedido')

    def test_duas_execucoes_apenas_um_post_e_um_historico(self):
        def executar(_):
            return seguro.realizar_pedido_seguro(Mock(), 1, 'teste', date(2026, 10, 6), 'almoco', date(2026, 10, 5))
        with patch.object(seguro, 'realizar_pedido', return_value=(True, 'Ticket gerado')) as post:
            with ThreadPoolExecutor(max_workers=8) as pool:
                resultados = list(pool.map(executar, range(8)))
            self.assertEqual(post.call_count, 1)
            self.assertEqual(sum(ok for ok, _ in resultados), 1)
        with psycopg.connect(self.url) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM pedido').fetchone()[0], 1)

    def test_crash_nao_libera_reserva(self):
        self.assertTrue(seguro.reservar(1, date(2026, 10, 6), 'almoco'))
        self.assertFalse(seguro.reservar(1, date(2026, 10, 6), 'almoco'))
        seguro.concluir(1, date(2026, 10, 6), 'almoco', 'incerto')
        self.assertFalse(seguro.reservar(1, date(2026, 10, 6), 'almoco'))

    def test_falha_segura_permite_nova_tentativa(self):
        self.assertTrue(seguro.reservar(1, date(2026, 10, 6), 'almoco'))
        seguro.concluir(1, date(2026, 10, 6), 'almoco', 'nao_enviado')
        self.assertTrue(seguro.reservar(1, date(2026, 10, 6), 'almoco'))
        self.assertTrue(seguro.reservar(1, date(2026, 10, 6), 'jantar'))
