import unittest
from unittest.mock import patch

from sistema_pedido import configuracao


class ConfiguracaoModoTesteTests(unittest.TestCase):
    def test_modo_teste_exige_prontuario(self):
        with (
            patch.object(configuracao, "MODO_TESTE", True),
            patch.object(configuracao, "PRONTUARIO_TESTE", ""),
        ):
            with self.assertRaisesRegex(ValueError, "PRONTUARIO_TESTE"):
                configuracao.validar_configuracao()

    def test_modo_teste_aceita_prontuario_informado(self):
        with (
            patch.object(configuracao, "MODO_TESTE", True),
            patch.object(configuracao, "PRONTUARIO_TESTE", "pt0000000"),
        ):
            configuracao.validar_configuracao()


if __name__ == "__main__":
    unittest.main()
