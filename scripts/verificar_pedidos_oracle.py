"""Verifica banco, SMTP e SICA sem fazer pedidos nem enviar mensagens."""
import json
import os
from pathlib import Path
import subprocess

config = Path('/home/ubuntu/.config/saborif/pedidos.json')
if not config.is_file():
    raise SystemExit('Configuracao de pedidos ainda nao instalada.')
if config.stat().st_mode & 0o077:
    raise SystemExit('Configuracao deve ter permissao 600.')
values = json.loads(config.read_text())
for key in ('DATABASE_URL', 'EMAIL_USER', 'EMAIL_PASS', 'TO_ADDRESS'):
    if not values.get(key):
        raise SystemExit('Falta configuracao: ' + key)

checks = '''
import os, smtplib, psycopg, requests
from sistema_pedido.configuracao import URL_PRINCIPAL
try:
    with psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=15) as conn:
        conn.execute('BEGIN READ ONLY')
        assert conn.execute('SELECT 1').fetchone()[0] == 1
        conn.execute('SELECT estado FROM envio_pedido LIMIT 0')
    print('Banco e estrutura: OK', flush=True)
    with smtplib.SMTP(os.environ.get('SMTP_SERVER') or 'smtp.gmail.com',
                      int(os.environ.get('SMTP_PORT') or 587), timeout=20) as smtp:
        smtp.starttls()
        smtp.login(os.environ['EMAIL_USER'], os.environ['EMAIL_PASS'])
    print('SMTP autenticado, sem enviar email: OK', flush=True)
    resposta = requests.get(URL_PRINCIPAL, timeout=20)
    resposta.raise_for_status()
    print('SICA acessivel, sem enviar pedido: OK', flush=True)
except Exception as erro:
    print('Falha no preflight: ' + type(erro).__name__, flush=True)
    raise SystemExit(1)
'''
command = ['docker', 'run', '--rm']
for key in values:
    command += ['-e', key]
command += ['saborif-pedidos:local', 'python', '-c', checks]
raise SystemExit(subprocess.run(command, env={**os.environ, **values}).returncode)
