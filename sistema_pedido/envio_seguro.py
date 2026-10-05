"""Coordena servidores sem repetir um envio de resultado desconhecido."""
from datetime import datetime
from pathlib import Path
import psycopg
from sistema_pedido.configuracao import URL_BANCO_DADOS, FUSO_HORARIO
from sistema_pedido.refeicoes import obter_refeicao
from sistema_pedido.utils import prazo_encerrado
from sistema_pedido.cliente_site import realizar_pedido, PedidoIncerto


def preparar_reservas():
    sql = (Path(__file__).resolve().parent.parent / 'migrations' /
           '003_reserva_envio.sql').read_text(encoding='utf-8')
    with psycopg.connect(URL_BANCO_DADOS, connect_timeout=15) as conn:
        conn.execute(sql)


def reservar(aluno_id, dia, refeicao):
    """A chave única decide o vencedor mesmo entre servidores concorrentes."""
    with psycopg.connect(URL_BANCO_DADOS, connect_timeout=15) as conn:
        row = conn.execute('''INSERT INTO envio_pedido
            (aluno_id, dia_pedido, refeicao, estado) VALUES (%s,%s,%s,'enviando')
            ON CONFLICT DO NOTHING RETURNING aluno_id''',
            (aluno_id, dia, refeicao)).fetchone()
        return row is not None


def concluir(aluno_id, dia, refeicao, estado, mensagem=''):
    with psycopg.connect(URL_BANCO_DADOS, connect_timeout=15) as conn:
        chave = (aluno_id, dia, refeicao)
        if estado == 'nao_enviado':
            conn.execute('''DELETE FROM envio_pedido WHERE
                aluno_id=%s AND dia_pedido=%s AND refeicao=%s''', chave)
        else:
            conn.execute('''UPDATE envio_pedido SET estado=%s, atualizado_em=now()
                WHERE aluno_id=%s AND dia_pedido=%s AND refeicao=%s''',
                (estado, *chave))
            if estado == 'confirmado':
                # Confirmação e histórico juntos. Uma falha não libera a reserva.
                conn.execute('''INSERT INTO pedido (aluno_id,dia_pedido,refeicao,motivo)
                    VALUES (%s,%s,%s,%s)''', (*chave, ('PEDIU_OK: ' + mensagem)[:800]))


def realizar_pedido_seguro(sessao, aluno_id, prontuario, dia, refeicao, data_execucao):
    nome = obter_refeicao(refeicao).nome
    if not reservar(aluno_id, dia, nome):
        return False, 'ENVIO_RESERVADO: outra execução enviou ou precisa confirmar no SICA.'

    def conferir_prazo():
        # Buscar o token também pode demorar; conferir imediatamente antes do POST.
        if prazo_encerrado(datetime.now(FUSO_HORARIO), data_execucao):
            raise ValueError('PRAZO_PERDIDO: nenhum pedido enviado após o limite.')

    try:
        ok, mensagem = realizar_pedido(sessao, prontuario, refeicao,
                                      antes_de_enviar=conferir_prazo)
    except PedidoIncerto:
        concluir(aluno_id, dia, nome, 'incerto')
        return False, 'ENVIO_INCERTO: verificar no SICA antes de tentar novamente.'
    # Exceção inesperada mantém a reserva. Não liberar por timeout ou crash.
    concluir(aluno_id, dia, nome, 'confirmado' if ok else 'nao_enviado', mensagem)
    return ok, mensagem
