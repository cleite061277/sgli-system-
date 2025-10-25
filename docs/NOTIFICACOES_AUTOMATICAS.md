# 📱 Sistema de Notificações Automáticas - SGLI

## 🎯 Visão Geral

Sistema completo de notificações automáticas que envia lembretes de vencimento de aluguel por **Email** e **WhatsApp**.

---

## ⚙️ Configuração

### 1. Configurar Email (Gmail)

Edite o arquivo `.env`:
```bash
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app
```

**Como obter senha de app:**
1. Acesse: https://myaccount.google.com/apppasswords
2. Selecione "Email" e "Outro dispositivo"
3. Copie a senha gerada

### 2. Configurar WhatsApp (Twilio)

Edite o arquivo `.env`:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

**Como obter credenciais Twilio:**
1. Cadastre-se: https://www.twilio.com/try-twilio (GRATUITO)
2. Verifique seu telefone
3. Copie Account SID e Auth Token do Console
4. Ative WhatsApp Sandbox

### 3. Ativar Notificações

No arquivo `.env`, altere:
```bash
NOTIFICACOES_ATIVAS=True
DIAS_ANTECEDENCIA_LEMBRETE=10
HORARIO_ENVIO=09:00
ENVIAR_EMAIL=True
ENVIAR_WHATSAPP=True
```

### 4. Configurar Agendamento
```bash
python manage.py configurar_agendamento
```

---

## 🚀 Iniciar Sistema

### Opção 1: Manualmente (Desenvolvimento)
```bash
./iniciar_worker.sh
```

Ou em background:
```bash
nohup ./iniciar_worker.sh > worker.log 2>&1 &
```

### Opção 2: Como Serviço (Produção)
```bash
sudo cp sgli_worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sgli_worker
sudo systemctl start sgli_worker
```

**Comandos úteis:**
```bash
# Ver status
sudo systemctl status sgli_worker

# Ver logs
sudo journalctl -u sgli_worker -f

# Parar
sudo systemctl stop sgli_worker

# Reiniciar
sudo systemctl restart sgli_worker
```

---

## 🧪 Testar Sistema

### Teste Manual de Envio
```bash
python manage.py enviar_lembretes
```

### Teste de Email
```python
from core.notifications import EmailSender

sender = EmailSender()
sucesso, msg = sender.testar_conexao()
print(msg)
```

### Teste de WhatsApp
```python
from core.notifications import WhatsAppSender

sender = WhatsAppSender()
sucesso, msg = sender.testar_conexao('+5511999999999')
print(msg)
```

---

## 📊 Monitoramento

### Ver Logs de Envio

1. Acesse: http://localhost:8000/admin/
2. Menu: **Logs de Notificações**
3. Filtre por data, tipo, status

### Ver Tarefas Agendadas

1. Acesse: http://localhost:8000/admin/
2. Menu: **Django Q** > **Scheduled tasks**

### Ver Histórico de Execuções

1. Acesse: http://localhost:8000/admin/
2. Menu: **Django Q** > **Successful tasks**

---

## ⚙️ Personalização

### Alterar Horário de Envio

Edite `.env`:
```bash
HORARIO_ENVIO=14:00  # 14h
```

Reconfigure:
```bash
python manage.py configurar_agendamento
```

### Alterar Dias de Antecedência

Edite `.env`:
```bash
DIAS_ANTECEDENCIA_LEMBRETE=7  # 7 dias antes
```

### Desativar Email ou WhatsApp

Edite `.env`:
```bash
ENVIAR_EMAIL=False  # Desativa email
ENVIAR_WHATSAPP=True  # Mantém WhatsApp
```

---

## 🔧 Solução de Problemas

### Worker não inicia
```bash
# Verificar logs
python manage.py qcluster --verbose

# Verificar banco
python manage.py migrate
```

### Emails não enviando
```bash
# Testar configuração SMTP
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Teste', 'Corpo', 'de@email.com', ['para@email.com'])
```

### WhatsApp não enviando
```bash
# Verificar credenciais Twilio
python manage.py shell
>>> from twilio.rest import Client
>>> client = Client('ACCOUNT_SID', 'AUTH_TOKEN')
>>> print(client.api.accounts.list())
```

### Notificações não executam

1. Verificar se worker está rodando: `ps aux | grep qcluster`
2. Verificar agendamento: Admin > Django Q > Scheduled tasks
3. Verificar se `NOTIFICACOES_ATIVAS=True` no .env

---

## 💰 Custos

### Email (Gmail)
- **Custo:** R$ 0,00 (GRATUITO)
- **Limite:** ~500 emails/dia

### WhatsApp (Twilio)
- **Custo:** ~R$ 0,025 por mensagem
- **30 mensagens/mês:** ~R$ 0,75/mês
- **Crédito inicial:** US$ 15 (gratuito no cadastro)

---

## 📝 Exemplo de Mensagem

### WhatsApp:
```
═══════════════════════════════
🏠 COMANDA DE ALUGUEL
═══════════════════════════════

📍 Imóvel: Rua das Flores, 123
👤 Locatário: João Silva
📅 Referência: Novembro/2025
📆 Vencimento: 10/11/2025

───────────────────────────────
💰 DETALHAMENTO
───────────────────────────────

Aluguel Base............R$ 1.200,00

───────────────────────────────
TOTAL A PAGAR.........R$ 1.200,00
═══════════════════════════════

⏰ Vence em 10 dias!

_Mensagem automática - SGLI System_
```

---

## ✅ Checklist de Ativação

- [ ] Configurar email no .env
- [ ] Configurar Twilio no .env
- [ ] Ativar notificações (NOTIFICACOES_ATIVAS=True)
- [ ] Executar: `python manage.py configurar_agendamento`
- [ ] Iniciar worker: `./iniciar_worker.sh`
- [ ] Testar envio: `python manage.py enviar_lembretes`
- [ ] Verificar logs no admin

---

© 2025 SGLI System - Sistema de Notificações Automáticas
