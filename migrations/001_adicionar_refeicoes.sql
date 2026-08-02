BEGIN;

-- Cada aluno pertence a uma unica refeicao. Registros antigos continuam como
-- almoco e a troca de refeicao nao altera dias ou pratos bloqueados.
ALTER TABLE aluno
    ADD COLUMN IF NOT EXISTS refeicao VARCHAR(10) NOT NULL DEFAULT 'almoco';

ALTER TABLE pedido
    ADD COLUMN IF NOT EXISTS refeicao VARCHAR(10) NOT NULL DEFAULT 'almoco';

-- Limpa a estrutura de uma versao de teste que guardava uma refeicao em cada
-- preferencia. Isso mantem a migracao segura mesmo se o rascunho foi executado.
ALTER TABLE preferencia_dia
    DROP CONSTRAINT IF EXISTS preferencia_dia_aluno_dia_refeicao_key;

ALTER TABLE preferencia_dia
    DROP CONSTRAINT IF EXISTS preferencia_dia_refeicao_check;

-- Se o rascunho chegou a ser testado, almoco e jantar podem ter criado duas
-- linhas para o mesmo dia. Mantemos apenas uma, pois o dia continua escolhido.
DELETE FROM preferencia_dia repetida
USING preferencia_dia mantida
WHERE repetida.aluno_id = mantida.aluno_id
  AND repetida.dia_semana = mantida.dia_semana
  AND repetida.ctid > mantida.ctid;

ALTER TABLE preferencia_dia
    DROP COLUMN IF EXISTS refeicao;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'preferencia_dia_aluno_id_dia_semana_key'
           AND conrelid = 'preferencia_dia'::regclass
    ) THEN
        ALTER TABLE preferencia_dia
            ADD CONSTRAINT preferencia_dia_aluno_id_dia_semana_key
            UNIQUE (aluno_id, dia_semana);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'aluno_refeicao_check'
           AND conrelid = 'aluno'::regclass
    ) THEN
        ALTER TABLE aluno
            ADD CONSTRAINT aluno_refeicao_check
            CHECK (refeicao IN ('almoco', 'jantar'));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'pedido_refeicao_check'
           AND conrelid = 'pedido'::regclass
    ) THEN
        ALTER TABLE pedido
            ADD CONSTRAINT pedido_refeicao_check
            CHECK (refeicao IN ('almoco', 'jantar'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS pedido_aluno_dia_refeicao_idx
    ON pedido (aluno_id, dia_pedido, refeicao);

COMMIT;
