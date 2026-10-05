import unicodedata
from datetime import datetime, timedelta
from sistema_pedido.configuracao import FUSO_HORARIO, HORA_CORTE, MINUTO_CORTE

DIAS_SEMANA_PT = {1: 'seg', 2: 'ter', 3: 'qua', 4: 'qui', 5: 'sex', 6: 'sab', 7: 'dom'}

def data_alvo_pedido(agora: datetime | None = None):
    """
    Calcula para qual dia o pedido deve ser feito.
    As duas tentativas mantêm o próximo dia útil como alvo.
    O prazo é validado separadamente; atraso nunca muda o alvo.
    Pula fins de semana.
    """
    if agora is None:
        agora = datetime.now(FUSO_HORARIO)
        
    agora = agora.astimezone(FUSO_HORARIO)
    data_alvo = (agora + timedelta(days=1)).date()
    
    # Se cair sábado (6) ou domingo (7), avança para segunda-feira
    while data_alvo.isoweekday() in (6, 7):
        data_alvo += timedelta(days=1)
        
    return data_alvo


def prazo_encerrado(agora=None, data_execucao=None):
    agora = (agora or datetime.now(FUSO_HORARIO)).astimezone(FUSO_HORARIO)
    if data_execucao is not None and agora.date() != data_execucao:
        return True
    return (agora.hour, agora.minute) >= (HORA_CORTE, MINUTO_CORTE)

def normalizar_texto(texto: str) -> str:
    """Remove acentos e converte para minúsculas para comparação fácil."""
    if not texto:
        return ""
    # Normaliza unicode (separando acentos das letras)
    nfkd = unicodedata.normalize('NFKD', texto)
    # Filtra apenas caracteres não-espaçamento (remove acentos)
    texto_sem_acento = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return texto_sem_acento.lower()

def verificar_bloqueios(texto_cardapio: str, lista_bloqueios: list[str]) -> tuple[bool, str]:
    """
    Verifica se o prato do dia contém algum item bloqueado pelo aluno.
    Retorna (True, "item_bloqueado") se encontrar, ou (False, "") se estiver limpo.
    """
    texto_base = normalizar_texto(texto_cardapio)
    encontrados = []
    
    for bloqueio in lista_bloqueios:
        bloqueio_norm = normalizar_texto(bloqueio)
        # Se o bloqueio existe e está contido no texto do prato
        if bloqueio_norm and bloqueio_norm in texto_base:
            encontrados.append(bloqueio)
            
    if encontrados:
        return True, ", ".join(encontrados)
    return False, ""
