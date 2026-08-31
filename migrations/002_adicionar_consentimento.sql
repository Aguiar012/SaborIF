BEGIN;

CREATE TABLE IF NOT EXISTS consentimento_uso_bot (
    id BIGSERIAL PRIMARY KEY,
    identificador_whatsapp VARCHAR(64) NOT NULL,
    versao_termo VARCHAR(32) NOT NULL,
    aceito_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT consentimento_uso_bot_identificador_versao_unico
        UNIQUE (identificador_whatsapp, versao_termo)
);

CREATE INDEX IF NOT EXISTS consentimento_uso_bot_identificador_idx
    ON consentimento_uso_bot (identificador_whatsapp);

COMMIT;