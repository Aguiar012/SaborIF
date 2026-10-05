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
4. Confirmar que Oracle e GitHub usam a versao atual com limite de horario.
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
terminarem. O GitHub continua ativo.
Nao iniciar manualmente os servicos para testar: eles fazem pedidos reais.
Atualizacoes posteriores do main reconstruem a imagem Python pelo deploy.

## Tentativas redundantes

Oracle e GitHub podem enviar novamente o pedido do mesmo aluno, inclusive
se o historico local ja indicar sucesso. O proprio SICA verifica duplicidade.
A resposta "Gerado anteriormente" e registrada como confirmacao, sem alerta
de falha. Timeout permite nova tentativa dentro do prazo, sem trava local.

A antiga tabela `envio_pedido` e a migracao 003 foram preservadas por historico,
mas nao sao mais consultadas ou usadas pelo programa. Nenhum historico de
pedidos ou cadastro foi apagado ao retirar a protecao.

Prazo perdido avisa somente pelo e-mail dos relatorios. O codigo 78 impede
o fallback de alerta no WhatsApp e ainda marca a execucao como falha.

## Teste sem pedidos reais

Os testes usam respostas simuladas: repeticao entre execucoes, timeout seguido
de ticket ja existente, registro da confirmacao e interrupcao apos o prazo.
Nao sao feitos pedidos reais, envios de mensagens ou alteracoes no banco.
