# 🏢 SGLI - Sistema de Gestão de Locação de Imóveis

## 📋 Visão Geral

Sistema completo para gerenciamento de locação de imóveis, desenvolvido em Django 4.2.8 com interface administrativa personalizada.

## 🚀 Versão: 1.0.0
**Data:** Outubro 2025  
**Ambiente:** Debian/Policorp  
**Linguagem:** Python 3.11  

---

## ✨ Funcionalidades Principais

### 👥 Gestão de Usuários
- **5 Tipos de usuário:**
  - 🔑 Administrador (acesso total)
  - 👨‍💼 Gerente (gestão operacional)
  - 👩‍💻 Atendente (cadastros e consultas)
  - 💰 Financeiro (pagamentos e relatórios)
  - 🏠 Locador (proprietário - visualização)

### 🏢 Gestão de Imóveis
- ✅ Cadastro completo de propriedades
- ✅ Fotos e documentos
- ✅ Status (Disponível, Locado, Manutenção)
- ✅ Histórico de locações

### 📄 Gestão de Contratos
- ✅ Geração automática de contratos
- ✅ Numeração sequencial
- ✅ Exportação em PDF e DOCX
- ✅ Cláusulas personalizáveis

### 💰 Gestão Financeira
- ✅ Controle de pagamentos
- ✅ Comandas automáticas
- ✅ Múltiplas formas de pagamento
- ✅ Relatórios financeiros

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Django 4.2.8
- **Banco de Dados:** SQLite (desenvolvimento) / PostgreSQL (produção)
- **Frontend Admin:** Django Admin customizado
- **Geração de Documentos:** 
  - ReportLab (PDF)
  - python-docx (DOCX)
- **Python:** 3.11

---

## 📦 Estrutura do Projeto
```
sgli_system/
├── core/                          # App principal
│   ├── models.py                  # Modelos do sistema
│   ├── admin.py                   # Configuração do admin
│   ├── views_gerar_contrato.py    # Views de contratos
│   ├── urls.py                    # Rotas da aplicação
│   └── templates/                 # Templates customizados
├── sgli_project/                  # Configurações Django
│   ├── settings.py                # Configurações principais
│   └── urls.py                    # Rotas principais
├── media/                         # Arquivos de usuários
├── static/                        # Arquivos estáticos
├── templates/                     # Templates globais
├── db.sqlite3                     # Banco de dados
└── manage.py                      # Gerenciador Django
```

---

## 🚀 Instalação

### 1. Requisitos
```bash
Python 3.11+
pip
virtualenv
```

### 2. Clonar e Configurar
```bash
# Extrair backup
tar -xzf sgli_backup_YYYYMMDD_HHMMSS.tar.gz
cd sgli_system

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configurar Banco
```bash
# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser
```

### 4. Executar
```bash
python manage.py runserver
```

Acesse: http://localhost:8000/admin/

---

## 👤 Usuários Padrão

**Admin:**
- Usuário: `admin`
- Senha: (definida na instalação)

---

## 📊 Modelos Principais

### Usuario (CustomUser)
- Campos: nome, email, tipo_usuario, telefone
- Tipos: ADMIN, GERENTE, ATENDENTE, FINANCEIRO, LOCADOR

### Locador
- Campos: nome/razao_social, cpf_cnpj, telefone, email
- Relacionamento: 1 Locador → N Imóveis

### Imovel
- Campos: codigo, endereco, tipo, area, valor_aluguel
- Status: Disponível, Locado, Manutenção

### Locatario
- Campos: nome/razao_social, cpf_cnpj, telefone, email
- Relacionamento: 1 Locatário → N Locações

### Locacao
- Campos: numero_contrato, imovel, locatario, datas, valores
- Status: Ativa, Finalizada, Cancelada
- **Funcionalidade:** Geração de contratos PDF/DOCX

### Comanda
- Campos: locacao, mes_referencia, valor_total
- Status: Pendente, Paga, Vencida, Cancelada

### Pagamento
- Campos: comanda, data, valor, forma_pagamento
- Status: Pendente, Confirmado, Estornado

---

## 📄 Geração de Contratos

### Botões no Admin
Ao abrir uma locação no admin, há dois botões:
- **📄 PDF:** Gera contrato em PDF (não editável)
- **📝 DOCX:** Gera contrato em Word (editável)

### URLs
```python
/contrato/<uuid>/pdf/   # Gera PDF
/contrato/<uuid>/docx/  # Gera DOCX
```

### Personalização
Edite os templates em:
- `core/views_gerar_contrato.py` (lógica)
- Variáveis do contrato no método da view

---

## 🔐 Segurança

- ✅ Autenticação obrigatória
- ✅ Permissões por tipo de usuário
- ✅ CSRF Protection
- ✅ SQL Injection Protection (Django ORM)
- ✅ XSS Protection

---

## 🔄 Backup e Restauração

### Backup Manual
```bash
# Backup do banco
python manage.py dumpdata > backup.json

# Backup de arquivos
tar -czf backup.tar.gz ~/sgli_system
```

### Restauração
```bash
# Restaurar banco
python manage.py loaddata backup.json

# Restaurar arquivos
tar -xzf backup.tar.gz
```

---

## 📞 Suporte

**Sistema:** SGLI v1.0  
**Desenvolvido para:** Policorp  
**Ambiente:** Debian GNU/Linux  

---

## 📝 Licença

© 2025 SGLI System - Todos os direitos reservados
