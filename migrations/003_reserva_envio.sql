-- Reserva persistente compartilhada entre Oracle e GitHub.
CREATE TABLE IF NOT EXISTS envio_pedido (
    aluno_id bigint NOT NULL REFERENCES aluno(id) ON DELETE CASCADE,
    dia_pedido date NOT NULL,
    refeicao text NOT NULL CHECK (refeicao IN ('almoco', 'jantar')),
    estado text NOT NULL CHECK (estado IN ('enviando', 'confirmado', 'incerto')),
    atualizado_em timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (aluno_id, dia_pedido, refeicao)
);
ALTER TABLE envio_pedido ENABLE ROW LEVEL SECURITY;
