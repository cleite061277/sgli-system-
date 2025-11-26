#!/bin/bash
# HABITAT PRO - Diagnóstico e Correção do Botão Dashboard no Admin
# Versão: 1.0
# Data: 2025-11-24
# 
# PROBLEMA: Botão "Dashboard Financeiro" não aparece nas Ações Rápidas do Admin

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║    HABITAT PRO - Diagnóstico Botão Dashboard Admin       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$HOME/sgli_system"
TEMPLATE_PATH="$PROJECT_DIR/core/templates/admin/index.html"

cd "$PROJECT_DIR"

echo -e "${BLUE}[DIAGNÓSTICO]${NC}"
echo ""

# 1. Verificar se template existe
echo -n "1. Template index.html existe... "
if [ -f "$TEMPLATE_PATH" ]; then
    echo -e "${GREEN}✅ SIM${NC}"
    SIZE=$(ls -lh "$TEMPLATE_PATH" | awk '{print $5}')
    echo "   Tamanho: $SIZE"
else
    echo -e "${RED}❌ NÃO ENCONTRADO${NC}"
    echo "   Esperado em: $TEMPLATE_PATH"
    echo ""
    echo -e "${YELLOW}SOLUÇÃO:${NC} Template precisa ser criado primeiro"
    exit 1
fi

# 2. Verificar diretório de templates
echo ""
echo -n "2. Diretório templates/admin... "
if [ -d "$PROJECT_DIR/core/templates/admin" ]; then
    echo -e "${GREEN}✅ EXISTE${NC}"
    ls -la "$PROJECT_DIR/core/templates/admin/" | grep -E "\.html$" | awk '{print "   " $9}' || echo "   (vazio)"
else
    echo -e "${RED}❌ NÃO EXISTE${NC}"
fi

# 3. Verificar conteúdo do template
echo ""
echo -n "3. Template tem botão Dashboard... "
if grep -q "Dashboard Financeiro" "$TEMPLATE_PATH" 2>/dev/null; then
    echo -e "${GREEN}✅ SIM${NC}"
else
    echo -e "${RED}❌ NÃO${NC}"
fi

# 4. Verificar settings.py
echo ""
echo -n "4. Configuração de TEMPLATES em settings.py... "
if grep -q "TEMPLATES" "$PROJECT_DIR/sgli/settings.py" 2>/dev/null; then
    echo -e "${GREEN}✅ ENCONTRADO${NC}"
    
    # Verificar se APP_DIRS está True
    if grep -A 10 "TEMPLATES" "$PROJECT_DIR/sgli/settings.py" | grep -q "'APP_DIRS': True"; then
        echo "   APP_DIRS: True ✅"
    else
        echo -e "   ${YELLOW}APP_DIRS: False ou não encontrado ⚠️${NC}"
    fi
else
    echo -e "${RED}❌ NÃO ENCONTRADO${NC}"
fi

# 5. Verificar ordem de apps
echo ""
echo -n "5. App 'core' em INSTALLED_APPS... "
if grep -A 20 "INSTALLED_APPS" "$PROJECT_DIR/sgli/settings.py" | grep -q "'core'"; then
    echo -e "${GREEN}✅ SIM${NC}"
    
    # Verificar posição
    POSITION=$(grep -n "INSTALLED_APPS" "$PROJECT_DIR/sgli/settings.py" | head -1 | cut -d: -f1)
    CORE_LINE=$(grep -n "'core'" "$PROJECT_DIR/sgli/settings.py" | head -1 | cut -d: -f1)
    ADMIN_LINE=$(grep -n "django.contrib.admin" "$PROJECT_DIR/sgli/settings.py" | head -1 | cut -d: -f1)
    
    if [ "$CORE_LINE" -lt "$ADMIN_LINE" ]; then
        echo -e "   ${GREEN}Posição: ANTES de django.contrib.admin ✅${NC}"
    else
        echo -e "   ${RED}Posição: DEPOIS de django.contrib.admin ❌${NC}"
        echo -e "   ${YELLOW}PROBLEMA: 'core' deve vir ANTES de 'django.contrib.admin'${NC}"
    fi
else
    echo -e "${RED}❌ NÃO${NC}"
fi

# 6. Verificar cache compilado
echo ""
echo -n "6. Cache de templates (.pyc)... "
PYC_COUNT=$(find "$PROJECT_DIR" -name "*.pyc" -type f 2>/dev/null | wc -l)
echo -e "${YELLOW}$PYC_COUNT arquivos${NC}"

echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}[CORREÇÃO AUTOMÁTICA]${NC}"
echo ""

# CORREÇÃO 1: Limpar cache
echo -n "1. Limpando cache de templates... "
find "$PROJECT_DIR" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_DIR" -type f -name '*.pyc' -delete 2>/dev/null || true
python manage.py collectstatic --clear --noinput > /dev/null 2>&1 || true
echo -e "${GREEN}✅ OK${NC}"

# CORREÇÃO 2: Verificar e corrigir INSTALLED_APPS
echo ""
echo "2. Verificando ordem de INSTALLED_APPS..."

CORE_BEFORE_ADMIN=$(python3 << 'PYTHON_EOF'
import re

try:
    with open('sgli/settings.py', 'r') as f:
        content = f.read()
    
    # Encontrar INSTALLED_APPS
    apps_match = re.search(r'INSTALLED_APPS\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if not apps_match:
        print("ERROR: INSTALLED_APPS não encontrado")
        exit(1)
    
    apps_content = apps_match.group(1)
    apps_lines = [line.strip().strip(',').strip("'\"") for line in apps_content.split('\n') if line.strip() and not line.strip().startswith('#')]
    
    # Encontrar posições
    try:
        core_pos = next(i for i, app in enumerate(apps_lines) if 'core' in app)
        admin_pos = next(i for i, app in enumerate(apps_lines) if 'django.contrib.admin' in app)
        
        if core_pos < admin_pos:
            print("OK")
        else:
            print("WRONG_ORDER")
    except StopIteration:
        print("NOT_FOUND")

except Exception as e:
    print(f"ERROR: {e}")
PYTHON_EOF
)

if [ "$CORE_BEFORE_ADMIN" = "OK" ]; then
    echo -e "   ${GREEN}✅ Ordem correta: 'core' antes de 'django.contrib.admin'${NC}"
elif [ "$CORE_BEFORE_ADMIN" = "WRONG_ORDER" ]; then
    echo -e "   ${RED}❌ Ordem incorreta!${NC}"
    echo ""
    echo -e "${YELLOW}   AÇÃO NECESSÁRIA:${NC}"
    echo "   Edite manualmente: $PROJECT_DIR/sgli/settings.py"
    echo "   Mova 'core' para ANTES de 'django.contrib.admin' em INSTALLED_APPS"
    echo ""
    echo "   Exemplo correto:"
    echo "   INSTALLED_APPS = ["
    echo "       'core',  # <-- Deve vir PRIMEIRO"
    echo "       'django.contrib.admin',"
    echo "       ..."
    echo "   ]"
else
    echo -e "   ${YELLOW}⚠️  Não foi possível verificar automaticamente${NC}"
fi

# CORREÇÃO 3: Reiniciar servidor
echo ""
echo "3. Próximo passo: Reiniciar servidor Django"
echo -e "   ${BLUE}Execute:${NC} python manage.py runserver"
echo ""

echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}DIAGNÓSTICO COMPLETO!${NC}"
echo ""
echo -e "${YELLOW}PRÓXIMOS PASSOS:${NC}"
echo ""
echo "1. Se INSTALLED_APPS está na ordem errada:"
echo "   nano sgli/settings.py"
echo "   Mova 'core' para ANTES de 'django.contrib.admin'"
echo ""
echo "2. Reinicie o servidor:"
echo "   python manage.py runserver"
echo ""
echo "3. Acesse o admin e force refresh:"
echo "   http://localhost:8000/admin/"
echo "   Pressione: Ctrl + Shift + R (force reload)"
echo ""
echo "4. Verifique se botão apareceu nas Ações Rápidas"
echo ""
