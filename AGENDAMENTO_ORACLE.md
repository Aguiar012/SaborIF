# Pedidos na Oracle

Os timers `saborif-pedidos@almoco.timer` e `saborif-pedidos@jantar.timer`
executam de segunda a sexta as 06h e 13h em America/Sao_Paulo.
Cada refeicao tem seu servico: systemd nao inicia outra instancia enquanto
a anterior estiver ativa. Nao ha recuperacao automatica de horarios perdidos
apos reiniciar a VM. O codigo bloqueia envios a partir das 13h15 e relata erro.

## Instalacao

1. Publicar o codigo e aguardar o deploy na Oracle.
2. Executar o workflow manual `Configurar pedidos na Oracle`.
   Ele usa os segredos existentes via SSH e prepara imagem/unidades, sem ativar.
3. Validar conexao ao banco, SMTP e SICA sem enviar pedidos:
   `python3 scripts/verificar_pedidos_oracle.py`.
4. Confirmar que Oracle e GitHub usam a versao com reserva de envio no banco.
5. Conferir que nao ha execucoes antigas de pedidos em andamento.
6. Ativar: `sudo systemctl enable --now saborif-pedidos@almoco.timer saborif-pedidos@jantar.timer`.

O GitHub permanece ativo como redundancia nos mesmos horarios. A antiga variavel
PEDIDOS_NA_ORACLE nao desativa mais os pedidos. As credenciais ficam em `/home/ubuntu/.config/saborif/pedidos.json`,
com permissao 600, fora do repositorio. Nao copiar esse arquivo para o GitHub.

## Conferir e reverter

`systemctl list-timers 'saborif-pedidos*'` mostra o proximo horario.
`journalctl -u saborif-pedidos@almoco.service` mostra a ultima execucao.
Os logs contem identificadores; devem permanecer com acesso restrito.

Para reverter: primeiro desativar ambos os timers e aguardar servicos ativos
terminarem. O GitHub continua ativo. Nao voltar a uma versao sem reservas
enquanto houver dois agendadores ou envios sem confirmacao.
Nao iniciar manualmente os servicos para testar: eles fazem pedidos reais.
Atualizacoes posteriores do main reconstruem a imagem Python pelo deploy.

## Protecao compartilhada

`envio_pedido` possui chave unica por aluno, data e refeicao. Antes do envio,
uma execucao reserva essa chave; as outras nao enviam. Sucesso e historico
sao gravados na mesma transacao. Erros comprovadamente anteriores ao POST
(como falha ao buscar o token) liberam a reserva para uma nova tentativa.

Timeout no POST, resposta desconhecida ou queda do processo deixam a reserva
como incerta ou enviando. Nao ha expiracao automatica: o SICA pode ter aceitado
o pedido. O relatorio por e-mail identifica esses casos. Conferir no SICA antes
de qualquer liberacao manual; jamais apagar reservas em massa. O procedimento
de recuperacao deve registrar a confirmacao no historico ou liberar apenas a
chave verificada como nao pedida, com ambos os agendadores parados.

Prazo perdido avisa somente pelo e-mail dos relatorios. O codigo 78 impede
o fallback de alerta no WhatsApp e ainda marca a execucao como falha.

## Teste sem pedidos reais

Os testes unitarios usam respostas simuladas. Com TEST_DATABASE_URL apontando
para um PostgreSQL DESCARTAVEL, os testes adicionais disputam a mesma reserva
com oito execucoes e verificam um unico envio simulado e um unico historico.
Esses testes limpam tabelas do banco de teste: nunca usar o banco de producao.
