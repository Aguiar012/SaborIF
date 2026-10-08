"""Interpreta resultados guardados, sem impedir novas tentativas no SICA."""
import re
import unicodedata


def classificar_resultado(motivo):
    texto = unicodedata.normalize('NFD', str(motivo or '').lower())
    texto = ''.join(c for c in texto if not unicodedata.combining(c)).strip()
    if texto.startswith(('cancelado_diretamente', 'cancelamento_email')):
        return 'CANCELADO'
    if texto.startswith(('nao_pediu:', 'nao pediu:')):
        return 'DISPENSADO'
    if texto.startswith('pediu_ok:'):
        return 'CONFIRMADO'
    # Registros antigos podem ter ERRO_PEDIDO mesmo com ticket existente.
    detalhe = texto.removeprefix('erro_pedido:').strip()
    detalhe = re.split(r'devido ao problema\s*:\s*', detalhe)[-1]
    detalhe = detalhe.strip().lstrip('×').strip()
    if re.fullmatch(
        r'(?:ticket\s+)?(?:gerado anteriormente|ja (?:foi )?(?:pedido|solicitado|gerado)|gerado(?: com sucesso)?)[.!\s]*',
        detalhe,
    ):
        return 'CONFIRMADO'
    return 'SEM_CONFIRMACAO'


def consolidar_resultados(motivos):
    """Recebe do mais novo ao mais antigo; falha técnica não desfaz um ticket."""
    tipos = [classificar_resultado(m) for m in motivos]
    for tipo in tipos:
        if tipo in ('CONFIRMADO', 'CANCELADO'):
            return tipo
    return tipos[0] if tipos else 'SEM_CONFIRMACAO'
