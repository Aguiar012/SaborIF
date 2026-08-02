import unittest
from pathlib import Path


CAMINHO_WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "main.yml"


class WorkflowRefeicoesTests(unittest.TestCase):
    def test_agendamentos_processam_almoco_e_jantar(self):
        workflow = CAMINHO_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("cron: '0 09 * * 1-5'", workflow)
        self.assertIn("cron: '0 16 * * 1-5'", workflow)
        self.assertIn("'[\"almoco\",\"jantar\"]'", workflow)
        self.assertIn("REFEICAO: ${{ matrix.refeicao }}", workflow)


if __name__ == "__main__":
    unittest.main()
