"""Definicoes compartilhadas de almoco e jantar."""

from dataclasses import dataclass
import unicodedata


@dataclass(frozen=True)
class Refeicao:
    """Identifica uma refeicao no bot e no formulario do SICA."""

    nome: str
    codigo_sica: str

    @property
    def titulo(self) -> str:
        return self.nome.capitalize()


ALMOCO = Refeicao(nome="almoco", codigo_sica="1")
JANTAR = Refeicao(nome="jantar", codigo_sica="2")


def obter_refeicao(valor: str | int | Refeicao | None) -> Refeicao:
    """Converte nomes e codigos conhecidos em uma refeicao valida."""
    if isinstance(valor, Refeicao):
        return valor

    texto = "almoco" if valor is None else str(valor).strip().lower()
    texto = "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caractere)
    )

    if texto in {"1", "almoco"}:
        return ALMOCO
    if texto in {"2", "janta", "jantar"}:
        return JANTAR

    raise ValueError(
        f"Refeicao invalida: {valor!r}. Use 'almoco' (1) ou 'jantar' (2)."
    )
