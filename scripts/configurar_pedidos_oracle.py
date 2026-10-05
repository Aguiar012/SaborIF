"""Importa segredos ja configurados no workflow via SSH, sem exibi-los."""
import json
import os
from pathlib import Path

keys = ('DATABASE_URL', 'EMAIL_USER', 'EMAIL_PASS', 'SMTP_SERVER', 'SMTP_PORT',
        'TO_ADDRESS', 'BOT_URL', 'BOT_API_KEY', 'ADMINS_E164')
values = {key: os.environ.get(key, '') for key in keys}
for key in ('DATABASE_URL', 'EMAIL_USER', 'EMAIL_PASS', 'TO_ADDRESS'):
    if not values[key]:
        raise SystemExit('Configuracao obrigatoria ausente: ' + key)
values['SMTP_SERVER'] = values['SMTP_SERVER'] or 'smtp.gmail.com'
values['SMTP_PORT'] = values['SMTP_PORT'] or '587'
folder = Path.home() / '.config' / 'saborif'
folder.mkdir(parents=True, exist_ok=True, mode=0o700)
os.chmod(folder, 0o700)
temp = folder / 'pedidos.json.tmp'
fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, 'w') as output:
    json.dump(values, output)
temp.replace(folder / 'pedidos.json')
print('Configuracao salva com acesso restrito.')
