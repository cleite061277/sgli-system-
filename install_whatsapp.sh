#!/bin/bash

# ═══════════════════════════════════════════════════════════
# INSTALAÇÃO AUTOMATIZADA - PAINEL WHATSAPP
# Execute: chmod +x install_whatsapp.sh && ./install_whatsapp.sh
# ═══════════════════════════════════════════════════════════

set -e  # Parar em caso de erro

echo "🚀 INSTALAÇÃO DO PAINEL WHATSAPP"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Verificar se estamos no diretório correto
if [ ! -f "manage.py" ]; then
    echo "❌ ERRO: Execute este script no diretório raiz do projeto (~/sgli_system)"
    exit 1
fi

echo "✅ Diretório correto detectado"
echo ""

# Criar backup
echo "📦 Criando backup..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "core/urls.py" ]; then
    cp core/urls.py "$BACKUP_DIR/urls.py.backup"
    echo "✅ Backup de urls.py criado"
fi

echo ""
echo "📁 Criando estrutura de diretórios..."
mkdir -p core
mkdir -p templates/core

echo "✅ Diretórios criados"
echo ""

# Verificar se arquivos de origem existem
if [ ! -f "views_whatsapp.py" ]; then
    echo "❌ ERRO: views_whatsapp.py não encontrado"
    echo "   Certifique-se de ter baixado todos os arquivos"
    exit 1
fi

if [ ! -f "painel_whatsapp.html" ]; then
    echo "❌ ERRO: painel_whatsapp.html não encontrado"
    echo "   Certifique-se de ter baixado todos os arquivos"
    exit 1
fi

# Copiar arquivos
echo "📄 Copiando arquivos..."

cp views_whatsapp.py core/views_whatsapp.py
echo "✅ views_whatsapp.py → core/views_whatsapp.py"

cp painel_whatsapp.html templates/core/painel_whatsapp.html
echo "✅ painel_whatsapp.html → templates/core/painel_whatsapp.html"

echo ""
echo "🔧 Integrando URLs..."

# Verificar se já foi integrado
if grep -q "views_whatsapp" core/urls.py 2>/dev/null; then
    echo "⚠️  URLs já parecem estar integradas, pulando..."
else
    # Criar arquivo temporário com as novas URLs
    cat > /tmp/urls_addition.txt << 'EOF'

# Painel WhatsApp - Adicionado automaticamente
from core.views_whatsapp import (
    painel_whatsapp,
    api_mensagem_comanda
)
EOF

    # Adicionar importações no topo do arquivo (após outras importações)
    sed -i '/from django.urls import/a\
\
# Painel WhatsApp\
from core.views_whatsapp import (\
    painel_whatsapp,\
    api_mensagem_comanda\
)' core/urls.py

    # Adicionar rotas no urlpatterns (antes do último colchete)
    sed -i '/^]/i\
\
    # Painel WhatsApp\
    path('\''admin/whatsapp/'\'', painel_whatsapp, name='\''painel_whatsapp'\''),\
    path('\''admin/whatsapp/comanda/<uuid:comanda_id>/mensagem/'\'', \
         api_mensagem_comanda, \
         name='\''api_mensagem_comanda'\''),' core/urls.py

    echo "✅ URLs integradas em core/urls.py"
fi

echo ""
echo "🧪 Testando sintaxe Python..."

# Testar sintaxe
python -m py_compile core/views_whatsapp.py 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Sintaxe Python válida"
else
    echo "❌ ERRO: Problema de sintaxe detectado"
    python -m py_compile core/views_whatsapp.py
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1. Testar localmente:"
echo "   python manage.py runserver"
echo "   Acesse: http://127.0.0.1:8000/admin/whatsapp/"
echo ""
echo "2. Se tudo estiver OK, faça o commit:"
echo "   git add core/views_whatsapp.py templates/core/painel_whatsapp.html core/urls.py"
echo "   git commit -m 'feat: Adiciona Painel WhatsApp'"
echo "   git push origin main"
echo ""
echo "3. Aguarde deploy no Railway (1-2 min)"
echo ""
echo "4. Acesse em produção:"
echo "   https://romantic-liberation-production.up.railway.app/admin/whatsapp/"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "💾 Backup salvo em: $BACKUP_DIR/"
echo ""
