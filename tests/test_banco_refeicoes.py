import unittest
from unittest.mock import MagicMock, patch

from sistema_pedido import banco_dados


def conexao_simulada(linhas=None):
    cursor = MagicMock()
    cursor.fetchall.return_value = linhas or []
    cursor.fetchone.return_value = (1,)

    contexto_cursor = MagicMock()
    contexto_cursor.__enter__.return_value = cursor

    conexao = MagicMock()
    conexao.cursor.return_value = contexto_cursor

    contexto_conexao = MagicMock()
    contexto_conexao.__enter__.return_value = conexao
    return contexto_conexao, cursor


class BancoRefeicoesTests(unittest.TestCase):
    def test_migracao_guarda_refeicao_no_aluno_e_mantem_dias_unicos(self):
        sql = banco_dados.CAMINHO_MIGRACAO_REFEICOES.read_text(encoding="utf-8")

        self.assertIn("ALTER TABLE aluno", sql)
        self.assertIn("ADD COLUMN IF NOT EXISTS refeicao", sql)
        self.assertIn("UNIQUE (aluno_id, dia_semana)", sql)
        self.assertIn("DROP COLUMN IF EXISTS refeicao", sql)

    @patch.object(banco_dados, "URL_BANCO_DADOS", "postgres://teste")
    @patch("sistema_pedido.banco_dados.psycopg.connect")
    def test_busca_alunos_somente_da_refeicao_escolhida(self, conectar):
        contexto, cursor = conexao_simulada([(10, "pt0000000")])
        conectar.return_value = contexto

        alunos = banco_dados.buscar_alunos_para_dia(2, "jantar")

        self.assertEqual(alunos, [{"id": 10, "prontuario": "pt0000000"}])
        sql, parametros = cursor.execute.call_args.args
        self.assertIn("a.refeicao = %s", sql)
        self.assertNotIn("p.refeicao", sql)
        self.assertEqual(parametros, [2, "jantar"])

    @patch.object(banco_dados, "URL_BANCO_DADOS", "postgres://teste")
    @patch("sistema_pedido.banco_dados.psycopg.connect")
    def test_modo_teste_filtra_um_unico_prontuario(self, conectar):
        contexto, cursor = conexao_simulada([(10, "3029701")])
        conectar.return_value = contexto

        banco_dados.buscar_alunos_para_dia(2, "jantar", "pt3029701")

        sql, parametros = cursor.execute.call_args.args
        self.assertIn("regexp_replace(a.prontuario", sql)
        self.assertEqual(parametros, [2, "jantar", "3029701"])

    @patch.object(banco_dados, "URL_BANCO_DADOS", "postgres://teste")
    @patch("sistema_pedido.banco_dados.psycopg.connect")
    def test_cancelamento_de_almoco_nao_cancela_jantar(self, conectar):
        contexto, cursor = conexao_simulada()
        conectar.return_value = contexto

        banco_dados.buscar_cancelamento_direto(10, "2026-08-03", "jantar")

        parametros = cursor.execute.call_args.args[1]
        self.assertEqual(parametros, (10, "2026-08-03", "jantar"))

    @patch.object(banco_dados, "URL_BANCO_DADOS", "postgres://teste")
    @patch("sistema_pedido.banco_dados.psycopg.connect")
    def test_historico_guarda_a_refeicao(self, conectar):
        contexto, cursor = conexao_simulada()
        conectar.return_value = contexto

        banco_dados.registrar_historico_pedido(
            10, "2026-08-03", "PEDIU_OK", "jantar"
        )

        parametros = cursor.execute.call_args.args[1]
        self.assertEqual(parametros, (10, "2026-08-03", "PEDIU_OK", "jantar"))


if __name__ == "__main__":
    unittest.main()
