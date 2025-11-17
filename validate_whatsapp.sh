#!/bin/bash

# ════════════════════════════════════════════════════════════
# VALIDAR INSTALAÇÃO DO PAINEL WHATSAPP
# ════════════════════════════════════════════════════════════

echo "🔍 VALIDANDO PAINEL WHATSAPP"
echo ""

cd ~/sgli_system
source venv/bin/activate

# ════════════════════════════════════════════════════════════
# 1. Verificar arquivos
# ════════════════════════════════════════════════════════════
echo "📁 [1/4] Verificando arquivos..."

if [ -f "core/views_whatsapp.py" ]; then
    echo "   ✅ core/views_whatsapp.py existe"
else
    echo "   ❌ core/views_whatsapp.py NÃO ENCONTRADO"
    echo ""
    echo "💡 Execute:"
    echo "   cp views_whatsapp.py core/views_whatsapp.py"
    exit 1
fi

if [ -f "templates/core/painel_whatsapp.html" ]; then
    echo "   ✅ templates/core/painel_whatsapp.html existe"
else
    echo "   ❌ templates/core/painel_whatsapp.html NÃO ENCONTRADO"
    echo ""
    echo "💡 Execute:"
    echo "   mkdir -p templates/core"
    echo "   cp painel_whatsapp.html templates/core/"
    exit 1
fi

# ════════════════════════════════════════════════════════════
# 2. Verificar URLs
# ════════════════════════════════════════════════════════════
echo ""
echo "🔗 [2/4] Verificando URLs..."

if grep -q "views_whatsapp" core/urls.py; then
    echo "   ✅ Importação encontrada em core/urls.py"
else
    echo "   ❌ Importação NÃO ENCONTRADA em core/urls.py"
    echo ""
    echo "💡 Adicione em core/urls.py:"
    echo "   from core.views_whatsapp import painel_whatsapp, api_mensagem_comanda"
    exit 1
fi

if grep -q "admin/whatsapp" core/urls.py; then
    echo "   ✅ Rota encontrada em core/urls.py"
else
    echo "   ❌ Rota NÃO ENCONTRADA em core/urls.py"
    echo ""
    echo "💡 Adicione em urlpatterns:"
    echo "   path('admin/whatsapp/', painel_whatsapp, name='painel_whatsapp'),"
    exit 1
fi

# ════════════════════════════════════════════════════════════
# 3. Verificar sintaxe Python
# ════════════════════════════════════════════════════════════
echo ""
echo "🐍 [3/4] Verificando sintaxe Python..."

python -m py_compile core/views_whatsapp.py 2>/dev/null

if [ $? -eq 0 ]; then
    echo "   ✅ Sintaxe Python OK"
else
    echo "   ❌ ERRO DE SINTAXE em views_whatsapp.py"
    python -m py_compile core/views_whatsapp.py
    exit 1
fi

# ════════════════════════════════════════════════════════════
# 4. Testar URL reversa
# ════════════════════════════════════════════════════════════
echo ""
echo "🧪 [4/4] Testando resolução de URL..."

python << 'PYEOF'
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgli_project.settings')

import django
django.setup()

from django.urls import reverse, NoReverseMatch

try:
    url = reverse('painel_whatsapp')
    print(f"   ✅ URL resolvida: {url}")
    
    # Testar importação das views
    from core.views_whatsapp import (
        painel_whatsapp,
        gerar_mensagem_whatsapp,
        api_mensagem_comanda
    )
    print("   ✅ Views importadas com sucesso")
    
except NoReverseMatch:
    print("   ❌ URL 'painel_whatsapp' não encontrada")
    print("")
    print("💡 Verifique se adicionou a rota em core/urls.py")
    sys.exit(1)
except ImportError as e:
    print(f"   ❌ Erro ao importar views: {e}")
    sys.exit(1)

PYEOF

if [ $? -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "✅ PAINEL WHATSAPP INSTALADO CORRETAMENTE!"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "🌐 ACESSO:"
    echo ""
    echo "  1. Inicie o servidor:"
    echo "     ./start_sgli.sh"
    echo ""
    echo "  2. Faça login no admin:"
    echo "     http://localhost:8000/admin/"
    echo "     Username: admin"
    echo "     Password: admin123"
    echo ""
    echo "  3. Acesse o Painel WhatsApp:"
    echo "     http://localhost:8000/admin/whatsapp/"
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "📋 O que você verá:"
    echo "  ✅ Dashboard com estatísticas de comandas"
    echo "  ✅ Filtros por mês e status"
    echo "  ✅ Lista de comandas com dados do locatário"
    echo "  ✅ Botões 'Copiar Mensagem' e 'Abrir WhatsApp'"
    echo ""
else
    echo ""
    echo "❌ Erro na validação. Verifique as mensagens acima."
fi
