import psycopg
import logging
from pathlib import Path
from sistema_pedido.configuracao import URL_BANCO_DADOS
from sistema_pedido.refeicoes import obter_refeicao


CAMINHO_MIGRACAO_REFEICOES = (
    Path(__file__).resolve().parent.parent
    / 'migrations'
    / '001_adicionar_refeicoes.sql'
)


def garantir_estrutura_refeicoes():
    """Aplica a migracao idempotente de almoco e jantar."""
    if not URL_BANCO_DADOS:
        return

    sql = CAMINHO_MIGRACAO_REFEICOES.read_text(encoding='utf-8')
    try:
        with psycopg.connect(URL_BANCO_DADOS) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(sql)
        logging.info("✅ Estrutura de almoco e jantar pronta.")
    except Exception as erro:
        logging.error(f"❌ Erro ao preparar estrutura de refeicoes: {erro}")
        raise


def buscar_cancelamento_direto(aluno_id: int, data_pedido, refeicao='almoco') -> bool:
    """
    Verifica se existe um pedido cancelado diretamente para este aluno nesta data.
    Retorna True se o aluno já cancelou (e portanto não devemos pedir).
    """
    if not URL_BANCO_DADOS:
        return False
        
    refeicao = obter_refeicao(refeicao)

    try:
        with psycopg.connect(URL_BANCO_DADOS) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("""
                    SELECT 1 
                      FROM pedido
                     WHERE aluno_id = %s
                       AND dia_pedido = %s
                       AND refeicao = %s
                       AND motivo LIKE 'CANCELADO_DIRETAMENTE%%';
                """, (aluno_id, data_pedido, refeicao.nome))
                resultado = cursor.fetchone()
                return resultado is not None
    except Exception as e:
        logging.error(f"Erro ao buscar cancelamento direto: {e}")
        return False

def buscar_alunos_para_dia(
    dia_da_semana: int, refeicao='almoco', prontuario: str | None = None
) -> list[dict]:
    """
    Busca alunos da refeicao escolhida no dia da semana especificado.
    
    Args:
        dia_da_semana (int): 1=Segunda, ..., 5=Sexta
    
    Returns:
        list[dict]: Lista de dicionários com 'id' e 'prontuario'.
    """
    if not URL_BANCO_DADOS:
        logging.error("❌ URL do banco não configurada!")
        return []

    refeicao = obter_refeicao(refeicao)
    alunos = []
    filtro_prontuario = ''
    parametros = [dia_da_semana, refeicao.nome]

    if prontuario:
        prontuario_sem_prefixo = prontuario.strip().lower()
        if prontuario_sem_prefixo.startswith('pt'):
            prontuario_sem_prefixo = prontuario_sem_prefixo[2:]
        filtro_prontuario = """
                       AND lower(regexp_replace(a.prontuario, '^pt', '', 'i')) = %s
        """
        parametros.append(prontuario_sem_prefixo)

    try:
        with psycopg.connect(URL_BANCO_DADOS) as conexao:
            with conexao.cursor() as cursor:
                # Seleciona alunos ativos que marcaram este dia da semana
                cursor.execute(f"""
                    SELECT DISTINCT a.id, a.prontuario
                      FROM aluno a
                      JOIN preferencia_dia p ON p.aluno_id = a.id
                     WHERE a.ativo = true
                       AND p.dia_semana = %s
                       AND a.refeicao = %s
                       {filtro_prontuario}
                     ORDER BY a.prontuario;
                """, parametros)
                
                for (id_aluno, prontuario) in cursor.fetchall():
                    alunos.append({'id': id_aluno, 'prontuario': prontuario})
                    
        return alunos
    except Exception as e:
        logging.error(f"❌ Erro no banco ao buscar alunos: {e}")
        return []

def buscar_telefone_aluno(aluno_id: int) -> str | None:
    """
    Busca o número de telefone vinculado a um aluno na tabela contato.
    Retorna o primeiro telefone encontrado ou None.
    """
    if not URL_BANCO_DADOS:
        return None

    try:
        with psycopg.connect(URL_BANCO_DADOS) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("""
                    SELECT telefone
                      FROM contato
                     WHERE aluno_id = %s
                     LIMIT 1;
                """, (aluno_id,))
                resultado = cursor.fetchone()
                return resultado[0] if resultado else None
    except Exception as e:
        logging.error(f"Erro ao buscar telefone do aluno {aluno_id}: {e}")
        return None

def buscar_pratos_bloqueados(prontuario: str) -> list[str]:
    """Retorna lista de nomes de pratos que o aluno bloqueou."""
    if not URL_BANCO_DADOS:
        return []

    try:
        with psycopg.connect(URL_BANCO_DADOS) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("""
                    SELECT pb.nome
                      FROM prato_bloqueado pb
                      JOIN aluno a ON a.id = pb.aluno_id
                     WHERE a.prontuario = %s
                     ORDER BY pb.nome;
                """, (prontuario,))
                # Retorna apenas uma lista de strings (ex: ['frango', 'peixe'])
                return [linha[0] for linha in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Erro ao buscar bloqueios do prontuário {prontuario}: {e}")
        return []

def registrar_historico_pedido(
    aluno_id: int, data_pedido, motivo: str, refeicao='almoco'
):
    """Salva no banco o resultado da tentativa de pedido (sucesso, erro ou pulo)."""
    if not URL_BANCO_DADOS:
        return

    refeicao = obter_refeicao(refeicao)

    # Corta o motivo para caber no banco se for muito grande
    motivo_seguro = (motivo or "")[:800]
    
    try:
        with psycopg.connect(URL_BANCO_DADOS) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO pedido (aluno_id, dia_pedido, motivo, refeicao)
                    VALUES (%s, %s, %s, %s)
                """, (aluno_id, data_pedido, motivo_seguro, refeicao.nome))
            conexao.commit()
    except Exception as e:
        logging.error(f"❌ Erro ao salvar histórico do pedido: {e}")

def atualizar_prato_dia(data_referencia, nome_prato: str):
    """
    Salva ou atualiza o prato do dia na tabela 'proximo_prato'.
    Isso permite que o Bot do WhatsApp saiba qual é o prato atual.
    """
    if not URL_BANCO_DADOS:
        return

    try:
        with psycopg.connect(URL_BANCO_DADOS) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO proximo_prato (dia_referente, prato_nome, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (dia_referente) 
                    DO UPDATE SET prato_nome = EXCLUDED.prato_nome, updated_at = NOW();
                """, (data_referencia, nome_prato))
            conexao.commit()
    except Exception as e:
        logging.error(f"❌ Erro ao salvar prato do dia no banco: {e}")

def buscar_prato_por_data(data_referencia) -> str | None:
    """
    Busca o prato salvo no banco para uma data específica.
    Retorna o nome do prato ou None se não encontrado.
    """
    if not URL_BANCO_DADOS:
        return None

    try:
        with psycopg.connect(URL_BANCO_DADOS) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("""
                    SELECT prato_nome
                      FROM proximo_prato
                     WHERE dia_referente = %s;
                """, (data_referencia,))
                resultado = cursor.fetchone()
                return resultado[0] if resultado else None
    except Exception as e:
        logging.error(f"Erro ao buscar prato por data {data_referencia}: {e}")
        return None
