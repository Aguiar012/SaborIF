# 🍽️ SaborIF - Bot de Refeições do IFSP Pirituba

Bot que **pede refeições automaticamente** no site SICA e permite o aluno **cancelar/gerenciar pelo WhatsApp**.

---

## 📁 Como o projeto está organizado

### 📌 Arquivos que VOCÊS vão mexer:

```
IFood/
│
├── �️ INICIAR_BOT_AQUI.bat          ← Clique duas vezes pra ligar o bot no Windows
├── 📄 .env                           ← Senhas e configurações secretas (criar manualmente)
├── 📄 ferramenta_corrigir_banco.js   ← Script pra consertar o banco se der problema
│
├── 📂 whatsapp/                      ← � CÓDIGO DO BOT WHATSAPP (JavaScript)
│   ├── 📂 bot/                          ← 🤖 O bot em si
│   │   ├── 📄 servidor_bot.js              ← ⭐ PRINCIPAL: conecta no WhatsApp
│   │   ├── 📄 logica_respostas.js          ← Decide o que responder pro aluno
│   │   └── 📄 refeicoes.js                 ← Regras de refeições e confirmações
│   └── 📄 configuracao_pastas.js        ← Define onde ficam os arquivos salvos
│
└── 📂 sistema_pedido/                ← 🍽️ CÓDIGO DOS PEDIDOS AUTOMÁTICOS (Python)
    ├── 📄 iniciar_pedidos.py            ← ⭐ PRINCIPAL: faz os pedidos no site
    ├── 📄 configuracao.py               ← URLs e tempos de espera
    ├── 📄 cliente_site.py               ← Acessa o site do refeitório
    ├── 📄 banco_dados.py                ← Lê e salva dados no banco
    ├── 📄 utils.py                      ← Funções auxiliares
    └── 📂 servicos/                     ← Avisos e notificações
        ├── 📄 email.py                     ← Envia e-mail
        └── 📄 whatsapp.py                  ← Avisa admins pelo WhatsApp
```

### 🚫 Arquivos que vocês NÃO precisam mexer:

> Esses arquivos são de **configuração automática**. O sistema precisa deles, mas vocês podem ignorar.

| Arquivo | Pra que serve (resumo) |
|---------|----------------------|
| `package.json` | Lista de bibliotecas do Node.js (tipo "lista de compras") |
| `package-lock.json` | Trava as versões das bibliotecas (gerado automaticamente) |
| `Dockerfile` | Receita pra rodar o projeto na nuvem com Docker |
| `docker-compose.yml` | Configuração do Docker no computador local |
| `fly.toml` | Configuração do servidor Fly.io (onde fica online) |
| `pm2_config.cjs` | Configuração do PM2 (mantém o bot ligado no servidor) |
| `.gitignore` | Diz pro Git quais arquivos NÃO subir pro GitHub |
| `.gitattributes` | Configuração visual do GitHub |

---

## 🚀 Como rodar no seu computador (passo a passo)

### Pré-requisitos
1. Instale o [Node.js](https://nodejs.org/) (versão 18 ou mais recente)
2. Tenha acesso ao banco de dados (peça a URL pro admin do projeto)

### Rodando o Bot WhatsApp

**Jeito fácil (Windows):**
1. Crie um arquivo `.env` na raiz do projeto com as variáveis necessárias (veja abaixo)
2. Clique duas vezes no arquivo `INICIAR_BOT_AQUI.bat` 🖱️
3. Escaneie o QR Code que aparece no terminal com seu WhatsApp

**Jeito pelo terminal:**
```bash
npm install
npm start
```

**Ver o QR Code no navegador:** Acesse `http://localhost:3001/qr`

### Rodando os pedidos automáticos (Python)
```bash
python -m sistema_pedido.iniciar_pedidos
```

---

## 🔑 Arquivo `.env` (variáveis secretas)

Crie um arquivo chamado `.env` na raiz do projeto com este conteúdo:

```env
# Banco de dados (OBRIGATÓRIO)
DATABASE_URL=postgres://usuario:senha@servidor:5432/nome_do_banco

# Email pra cancelamento (opcional)
GMAIL_USER=seu_email@gmail.com
GMAIL_APP_PASSWORD=sua_senha_de_app
CAE_EMAIL=email_da_cae@ifsp.edu.br

# Proxy (só se precisar)
PROXY_URL=
```

> ⚠️ **NUNCA** suba o `.env` pro GitHub! Ele já está no `.gitignore`.

---

## 🛠️ Como funciona por dentro

### Bot WhatsApp (Node.js)
1. `servidor_bot.js` conecta no WhatsApp usando a biblioteca Baileys
2. Quando alguém manda mensagem, passa pro `logica_respostas.js`
3. Se a mensagem não bate com nenhum comando, reexibe o menu principal interativo

### Pedidos Automáticos (Python)
1. `iniciar_pedidos.py` roda todo dia de manhã (agendado)
2. Busca no banco quem quer almoçar naquele dia
3. Acessa o site do refeitório e faz o pedido pra cada aluno
4. Avisa os admins se der algum erro

---

## 🐛 Problemas comuns

| Problema | Solução |
|----------|---------|
| Bot não conecta | Apague a pasta `dados_bot/auth` e escaneie o QR de novo |
| Erro de banco de dados | Verifique se `DATABASE_URL` está no `.env` |
| QR Code não aparece | Acesse `http://localhost:3001/qr` no navegador |
| Bot parou do nada | Rode `npm start` de novo ou use o `.bat` |

---

## 📦 Deploy (subir pra nuvem)

O projeto usa [Fly.io](https://fly.io). Para fazer deploy:

```bash
fly deploy
```

Para rodar com PM2 em servidor próprio:
```bash
pm2 start whatsapp/pm2_config.cjs
```
