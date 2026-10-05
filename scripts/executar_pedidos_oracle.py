"""Executado pelo systemd. Segredos ficam fora do repositorio e dos argumentos."""
import json
import os
import subprocess
import sys
from pathlib import Path

refeicao = sys.argv[1]
if refeicao not in ('almoco', 'jantar'):
    raise SystemExit('Refeicao invalida')
config = Path('/home/ubuntu/.config/saborif/pedidos.json')
env = {**os.environ, **json.loads(config.read_text())}
env.update(REFEICAO=refeicao, MODO_TESTE='false', SIMULAR_PEDIDO='false')
command = ['docker', 'run', '--rm', '--name', 'saborif-pedidos-' + refeicao]
for key in json.loads(config.read_text()):
    command += ['-e', key]
command += ['-e', 'REFEICAO', '-e', 'MODO_TESTE', '-e', 'SIMULAR_PEDIDO',
            'saborif-pedidos:local']
raise SystemExit(subprocess.run(command, env=env).returncode)
