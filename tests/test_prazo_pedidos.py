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
        with patch.object(app, 'SIMULAR_PEDIDO', False), patch.object(app, 'prazo_encerrado', return_value=True), patch.object(app, 'enviar_email') as email, patch.object(app, 'garantir_estrutura_refeicoes') as migrar, patch.object(app, 'buscar_cardapio_site') as sica:
            with self.assertRaisesRegex(RuntimeError, 'Prazo perdido'):
                app.principal()
            email.assert_called_once()
            migrar.assert_not_called()
            sica.assert_not_called()

    def executar_cenario(self, confirmado, limite, enviar):
        from contextlib import ExitStack
        with ExitStack() as stack:
            mocks = {}
            retornos = {
                'validar_configuracao': None, 'garantir_estrutura_refeicoes': None, 'preparar_reservas': None,
                'buscar_cardapio_site': 'arroz',
                'buscar_alunos_para_dia': [{'id': 1, 'prontuario': 'teste'}],
                'buscar_cancelamento_direto': False, 'pedido_ja_realizado': confirmado,
                'buscar_pratos_bloqueados': [], 'registrar_historico_pedido': None,
                'enviar_email': None, 'notificar_administradores': None,
                'realizar_pedido_seguro': (True, 'Ticket gerado'),
            }
            for nome, retorno in retornos.items():
                mocks[nome] = stack.enter_context(patch.object(app, nome, return_value=retorno))
            stack.enter_context(patch.object(app, 'SIMULAR_PEDIDO', False))
            stack.enter_context(patch.object(app.time, 'sleep'))
            stack.enter_context(patch.object(app, 'prazo_encerrado', side_effect=[False, limite]))
            if limite and not confirmado:
                with self.assertRaisesRegex(RuntimeError, 'Prazo perdido durante'):
                    app.principal()
                self.assertIn('PRAZO_PERDIDO', mocks['registrar_historico_pedido'].call_args.args[2])
            else:
                app.principal()
            self.assertEqual(mocks['realizar_pedido_seguro'].call_count, enviar)

    def test_segunda_tentativa_nao_reenvia_sucesso(self):
        self.executar_cenario(confirmado=True, limite=False, enviar=0)

    def test_prazo_vence_durante_pausa_e_impede_post(self):
        self.executar_cenario(confirmado=False, limite=True, enviar=0)

    def test_pendente_antes_do_prazo_e_enviado(self):
        self.executar_cenario(confirmado=False, limite=False, enviar=1)
