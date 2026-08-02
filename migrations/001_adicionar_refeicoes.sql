BEGIN;

-- Registros antigos continuam sendo almoco. O valor padrao tambem protege
-- versoes antigas do bot durante uma atualizacao gradual.
ALTER TABLE preferencia_dia
    ADD COLUMN IF NOT EXISTS refeicao VARCHAR(10) NOT NULL DEFAULT 'almoco';

ALTER TABLE pedido
    ADD COLUMN IF NOT EXISTS refeicao VARCHAR(10) NOT NULL DEFAULT 'almoco';

-- Antes, um aluno so podia ter uma preferencia por dia. Agora ele pode ter
-- uma de almoco e outra de jantar no mesmo dia.
ALTER TABLE preferencia_dia
    DROP CONSTRAINT IF EXISTS preferencia_dia_aluno_id_dia_semana_key;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'preferencia_dia_aluno_dia_refeicao_key'
           AND conrelid = 'preferencia_dia'::regclass
    ) THEN
        ALTER TABLE preferencia_dia
            ADD CONSTRAINT preferencia_dia_aluno_dia_refeicao_key
            UNIQUE (aluno_id, dia_semana, refeicao);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'preferencia_dia_refeicao_check'
           AND conrelid = 'preferencia_dia'::regclass
    ) THEN
        ALTER TABLE preferencia_dia
            ADD CONSTRAINT preferencia_dia_refeicao_check
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
