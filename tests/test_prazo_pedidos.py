import unittest
from datetime import datetime, date
from unittest.mock import patch
from zoneinfo import ZoneInfo
from sistema_pedido.utils import data_alvo_pedido, prazo_encerrado
from sistema_pedido import iniciar_pedidos as app

SP = ZoneInfo('America/Sao_Paulo')

class PrazoTests(unittest.TestCase):
    def test_prazo_perdido_nao_dispara_whatsapp_fatal(self):
        with patch.object(app, 'principal', side_effect=app.PrazoPerdido('Prazo perdido')), patch.object(app, 'notificar_administradores') as admins, patch.object(app, 'enviar_mensagem_aluno') as aluno:
            with self.assertRaises(SystemExit) as resultado:
                app.executar()
            self.assertEqual(resultado.exception.code, 78)
            admins.assert_not_called()
            aluno.assert_not_called()

    def test_atraso_nao_muda_terca_para_quarta(self):
        for hora, minuto in [(6, 0), (13, 0), (14, 45)]:
            self.assertEqual(data_alvo_pedido(datetime(2026, 10, 5, hora, minuto, tzinfo=SP)), date(2026, 10, 6))

    def test_limite_e_fim_de_semana(self):
        self.assertFalse(prazo_encerrado(datetime(2026, 10, 5, 13, 14, 59, tzinfo=SP)))
        self.assertTrue(prazo_encerrado(datetime(2026, 10, 5, 13, 15, tzinfo=SP)))
        self.assertTrue(prazo_encerrado(datetime(2026, 10, 6, 6, tzinfo=SP), date(2026, 10, 5)))
        self.assertEqual(data_alvo_pedido(datetime(2026, 10, 9, 6, tzinfo=SP)), date(2026, 10, 12))

    def test_inicio_atrasado_alerta_sem_acessar_sica_ou_migrar(self):
        with patch.object(app, 'validar_configuracao'), patch.object(app, 'buscar_alunos_para_dia', return_value=[{'id': 1}]), patch.object(app, 'buscar_resultados_dia', return_value={}), patch.object(app, 'SIMULAR_PEDIDO', False), patch.object(app, 'prazo_encerrado', return_value=True), patch.object(app, 'enviar_email') as email, patch.object(app, 'garantir_estrutura_refeicoes') as migrar, patch.object(app, 'buscar_cardapio_site') as sica:
            with self.assertRaisesRegex(RuntimeError, 'Prazo perdido'):
                app.principal()
            email.assert_called_once()
            migrar.assert_not_called()
            sica.assert_not_called()

    def executar_cenario(self, limite, enviar, resposta=None, execucoes=1, confirmado_antes=False):
        from contextlib import ExitStack
        with ExitStack() as stack:
            mocks = {}
            retornos = {
                'validar_configuracao': None, 'garantir_estrutura_refeicoes': None,
                'buscar_cardapio_site': 'arroz',
                'buscar_alunos_para_dia': [{'id': 1, 'prontuario': 'teste'}],
                'buscar_cancelamento_direto': False,
                'buscar_resultados_dia': {1: 'CONFIRMADO'} if confirmado_antes else {},
                'buscar_pratos_bloqueados': [], 'registrar_historico_pedido': None,
                'enviar_email': None, 'notificar_administradores': None,
                'realizar_pedido': resposta or (True, 'Ticket gerado'),
            }
            for nome, retorno in retornos.items():
                mocks[nome] = stack.enter_context(patch.object(app, nome, return_value=retorno))
            stack.enter_context(patch.object(app, 'SIMULAR_PEDIDO', False))
            stack.enter_context(patch.object(app.time, 'sleep'))
            stack.enter_context(patch.object(app, 'prazo_encerrado', side_effect=[False, limite] * execucoes))
            if limite and not confirmado_antes:
                with self.assertRaisesRegex(RuntimeError, 'Prazo perdido durante'):
                    app.principal()
                self.assertIn('PRAZO_PERDIDO', mocks['registrar_historico_pedido'].call_args.args[2])
            else:
                for _ in range(execucoes):
                    app.principal()
            self.assertEqual(mocks['realizar_pedido'].call_count, enviar)
            if confirmado_antes:
                self.assertIn('PEDIU_OK:', mocks['registrar_historico_pedido'].call_args.args[2])
                self.assertNotIn('PRAZO_PERDIDO', mocks['enviar_email'].call_args.args[1])
                mocks['notificar_administradores'].assert_not_called()
            if resposta and resposta[0]:
                self.assertIn('PEDIU_OK:', mocks['registrar_historico_pedido'].call_args.args[2])
                mocks['notificar_administradores'].assert_not_called()

    def test_segunda_execucao_reenvia_para_sica_validar(self):
        self.executar_cenario(limite=False, enviar=2, execucoes=2)

    def test_ja_pedido_e_registrado_como_sucesso_sem_alerta(self):
        self.executar_cenario(limite=False, enviar=1, resposta=(True, 'Gerado anteriormente'))

    def test_prazo_vence_durante_pausa_e_impede_post(self):
        self.executar_cenario(limite=True, enviar=0)

    def test_prazo_vence_mas_ticket_anterior_ja_esta_confirmado(self):
        self.executar_cenario(limite=True, enviar=0, confirmado_antes=True)

    def test_pendente_antes_do_prazo_e_enviado(self):
        self.executar_cenario(limite=False, enviar=1)
