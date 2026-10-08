import unittest
from datetime import datetime, date
from unittest.mock import patch
from zoneinfo import ZoneInfo
from sistema_pedido.historico import classificar_resultado, consolidar_resultados
from sistema_pedido import iniciar_pedidos as app
from sistema_pedido import banco_dados as banco
from test_banco_refeicoes import conexao_simulada


class HistoricoTests(unittest.TestCase):
    def test_ticket_existente_com_cabecalho_negativo_e_prefixo_antigo(self):
        texto = 'ERRO_PEDIDO: × Que pena! O ticket de hoje nao foi gerado devido ao problema: Gerado anteriormente.'
        self.assertEqual(classificar_resultado(texto), 'CONFIRMADO')
        for texto in ['ERRO_PEDIDO: não gerado anteriormente',
                      'ERRO_PEDIDO: Ticket gerado anteriormente não encontrado',
                      'ERRO_PEDIDO: prazo encerrado', 'ERRO_PEDIDO: timeout']:
            self.assertEqual(classificar_resultado(texto), 'SEM_CONFIRMACAO')

    def test_falha_nao_apaga_sucesso_e_cancelamento_posterior_prevalece(self):
        self.assertEqual(consolidar_resultados(['ERRO_PEDIDO: timeout', 'PEDIU_OK: Ticket gerado']), 'CONFIRMADO')
        self.assertEqual(consolidar_resultados(['CANCELAMENTO_EMAIL: enviado', 'PEDIU_OK: Ticket gerado']), 'CANCELADO')
        self.assertEqual(consolidar_resultados(['PEDIU_OK: Ticket gerado', 'CANCELADO_DIRETAMENTE: antigo']), 'CONFIRMADO')
        self.assertEqual(consolidar_resultados([]), 'SEM_CONFIRMACAO')

    def test_consulta_isola_data_e_refeicao_e_consolida_por_aluno(self):
        contexto, cursor = conexao_simulada([(1, 'ERRO_PEDIDO: timeout'), (2, 'CANCELADO_DIRETAMENTE: aluno'), (1, 'PEDIU_OK: Ticket gerado')])
        with patch.object(banco, 'URL_BANCO_DADOS', 'teste'), patch.object(banco.psycopg, 'connect', return_value=contexto):
            resultado = banco.buscar_resultados_dia(date(2026, 10, 8), 'jantar')
        self.assertEqual(resultado, {1: 'CONFIRMADO', 2: 'CANCELADO'})
        sql, params = cursor.execute.call_args.args
        self.assertIn('ORDER BY id DESC', sql)
        self.assertEqual(params, (date(2026, 10, 8), 'jantar'))

    def conferir_atraso(self, resultados, falha=None):
        agora = datetime(2026, 10, 7, 17, 56, tzinfo=ZoneInfo('America/Sao_Paulo'))
        with patch.object(app, 'buscar_alunos_para_dia', return_value=[{'id': 1}, {'id': 2}]), patch.object(app, 'buscar_resultados_dia', return_value=resultados, side_effect=falha), patch.object(app, 'enviar_email') as email, patch.object(app, 'realizar_pedido') as pedir, patch.object(app, 'notificar_administradores') as zap:
            try:
                app.conferir_execucao_atrasada(agora, date(2026, 10, 8))
            except app.PrazoPerdido:
                pass
            pedir.assert_not_called()
            zap.assert_not_called()
            return email

    def test_atraso_com_confirmacoes_ou_cancelamentos_nao_alerta(self):
        self.conferir_atraso({1: 'CONFIRMADO', 2: 'CONFIRMADO'}).assert_not_called()
        self.conferir_atraso({1: 'CONFIRMADO', 2: 'CANCELADO'}).assert_not_called()
        self.conferir_atraso({1: 'CONFIRMADO', 2: 'DISPENSADO'}).assert_not_called()

    def test_atraso_parcial_alerta_apenas_pendentes(self):
        email = self.conferir_atraso({1: 'CONFIRMADO'})
        email.assert_called_once()
        self.assertIn('1 de 2 alunos programados sem confirmação', email.call_args.args[1])

    def test_banco_indisponivel_nao_e_tratado_como_pedido_perdido(self):
        email = self.conferir_atraso({}, RuntimeError('offline'))
        self.assertIn('verificação indisponível', email.call_args.args[0])
        self.assertNotIn('prazo perdido', email.call_args.args[0])
