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
3. Validar conexao ao banco, SMTP e SICA sem enviar pedidos.
4. Definir a variavel do repositorio `PEDIDOS_NA_ORACLE=true`.
5. Conferir que nao ha execucoes de pedidos no GitHub em andamento.
6. Ativar: `sudo systemctl enable --now saborif-pedidos@almoco.timer saborif-pedidos@jantar.timer`.

O workflow do GitHub permite apenas simulacoes manuais enquanto essa variavel
estiver ativa. As credenciais ficam em `/home/ubuntu/.config/saborif/pedidos.json`,
com permissao 600, fora do repositorio. Nao copiar esse arquivo para o GitHub.

## Conferir e reverter

`systemctl list-timers 'saborif-pedidos*'` mostra o proximo horario.
`journalctl -u saborif-pedidos@almoco.service` mostra a ultima execucao.
Os logs contem identificadores; devem permanecer com acesso restrito.

Para reverter: primeiro desativar ambos os timers e aguardar servicos ativos
terminarem. So entao remover a variavel PEDIDOS_NA_ORACLE do GitHub.
Nao iniciar manualmente os servicos para testar: eles fazem pedidos reais.
Atualizacoes posteriores do main reconstruem a imagem Python pelo deploy.
