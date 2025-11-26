#!/bin/bash
################################################################################
#                                                                              #
#  🚀 INSTALAÇÃO COMPLETA - DASHBOARD FINANCEIRO (V2 - CORRIGIDA)              #
#                                                                              #
#  Versão sem verificação de imports (etapa 6 removida)                       #
#                                                                              #
################################################################################

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
RESET='\033[0m'

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups_dashboard_${TIMESTAMP}"
ERRO=0

print_header() {
    echo ""
    echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════════${RESET}"
    echo -e "${BLUE}${BOLD}  $1${RESET}"
    echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════════${RESET}"
    echo ""
}

print_success() { echo -e "${GREEN}✅ $1${RESET}"; }
print_error() { echo -e "${RED}❌ $1${RESET}"; ERRO=1; }
print_warning() { echo -e "${YELLOW}⚠️  $1${RESET}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${RESET}"; }
print_step() { echo -e "${CYAN}${BOLD}[$1] $2${RESET}"; }

clear
print_header "🚀 INSTALAÇÃO COMPLETA - DASHBOARD FINANCEIRO V2"

echo -e "${CYAN}Timestamp: ${TIMESTAMP}${RESET}"
echo ""

# ====== VERIFICAÇÕES INICIAIS ======
print_step "1/7" "VERIFICAÇÕES INICIAIS"
echo ""

if [ ! -f "manage.py" ]; then
    print_error "manage.py não encontrado!"
    print_info "Execute: cd ~/sgli_system"
    exit 1
fi
print_success "Diretório correto: $(pwd)"

ARQUIVOS_NECESSARIOS=("urls.py" "dashboard_views.py" "index.html" "views_relatorios.py")
for arquivo in "${ARQUIVOS_NECESSARIOS[@]}"; do
    if [ ! -f "$arquivo" ]; then
        print_error "Arquivo não encontrado: $arquivo"
        print_info "Copie: cp ~/Downloads/$arquivo ."
        exit 1
    fi
    print_success "$arquivo encontrado"
done

# ====== CRIAR BACKUPS ======
print_step "2/7" "CRIANDO BACKUPS"
echo ""

mkdir -p "$BACKUP_DIR"
print_success "Diretório criado: $BACKUP_DIR"

ARQUIVOS_BACKUP=(
    "core/urls.py"
    "core/dashboard_views.py"
    "core/views_relatorios.py"
    "core/templates/admin/index.html"
)

for arquivo in "${ARQUIVOS_BACKUP[@]}"; do
    if [ -f "$arquivo" ]; then
        BACKUP_PATH="$BACKUP_DIR/$arquivo"
        mkdir -p "$(dirname "$BACKUP_PATH")"
        cp "$arquivo" "$BACKUP_PATH"
        print_success "✓ $arquivo → $BACKUP_PATH"
    fi
done

# ====== VALIDAR SINTAXE ======
print_step "3/7" "VALIDANDO SINTAXE"
echo ""

for arquivo in urls.py dashboard_views.py views_relatorios.py; do
    python -m py_compile "$arquivo" 2>&1
    if [ $? -ne 0 ]; then
        print_error "Erro de sintaxe em $arquivo"
        exit 1
    fi
    print_success "✓ $arquivo (sintaxe OK)"
done

# ====== INSTALAR ARQUIVOS ======
print_step "4/7" "INSTALANDO ARQUIVOS"
echo ""

cp urls.py core/urls.py && print_success "✓ core/urls.py"
cp dashboard_views.py core/dashboard_views.py && print_success "✓ core/dashboard_views.py"
cp views_relatorios.py core/views_relatorios.py && print_success "✓ core/views_relatorios.py (CORRIGIDO)"

mkdir -p core/templates/admin
cp index.html core/templates/admin/index.html && print_success "✓ core/templates/admin/index.html"

# ====== VALIDAR DJANGO ======
print_step "5/7" "VALIDANDO DJANGO"
echo ""

python manage.py check > /tmp/check_$$.log 2>&1
RESULTADO=$?

if [ $RESULTADO -eq 0 ]; then
    print_success "✓ Sistema Django validado sem erros!"
else
    print_error "Django check encontrou erros:"
    cat /tmp/check_$$.log
    rm /tmp/check_$$.log
    
    print_warning "Tentando reverter instalação..."
    if [ -d "$BACKUP_DIR" ]; then
        cp "$BACKUP_DIR/core/urls.py" core/ 2>/dev/null
        cp "$BACKUP_DIR/core/dashboard_views.py" core/ 2>/dev/null
        cp "$BACKUP_DIR/core/views_relatorios.py" core/ 2>/dev/null
        print_info "Backups restaurados"
    fi
    exit 1
fi
rm /tmp/check_$$.log

# ====== CRIAR ROLLBACK ======
print_step "6/7" "CRIANDO SCRIPT DE ROLLBACK"
echo ""

ROLLBACK="rollback_dashboard_${TIMESTAMP}.sh"

cat > "$ROLLBACK" << EOF
#!/bin/bash
# Rollback automático - Dashboard Financeiro
# Gerado: ${TIMESTAMP}

echo "⚠️  Iniciando rollback..."

if [ -d "$BACKUP_DIR" ]; then
    cp $BACKUP_DIR/core/urls.py core/
    cp $BACKUP_DIR/core/dashboard_views.py core/
    cp $BACKUP_DIR/core/views_relatorios.py core/
    rm -f core/templates/admin/index.html
    
    echo "✅ Rollback concluído!"
    echo ""
    echo "Validando..."
    python manage.py check
else
    echo "❌ Backup não encontrado: $BACKUP_DIR"
    exit 1
fi
EOF

chmod +x "$ROLLBACK"
print_success "✓ Script criado: $ROLLBACK"

# ====== RELATÓRIO ======
print_step "7/7" "RELATÓRIO FINAL"
echo ""

echo -e "${BOLD}📋 ARQUIVOS MODIFICADOS:${RESET}"
echo "  • core/urls.py"
echo "  • core/dashboard_views.py"
echo "  • core/views_relatorios.py (4 funções adicionadas)"
echo "  • core/templates/admin/index.html (criado)"

echo ""
echo -e "${BOLD}📂 BACKUP:${RESET}"
echo "  📁 $BACKUP_DIR"

echo ""
echo -e "${BOLD}🔄 ROLLBACK:${RESET}"
echo "  📜 ./$ROLLBACK"

# ====== SUCESSO ======
print_header "🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!"

echo -e "${GREEN}${BOLD}✅ Dashboard Financeiro instalado e pronto para uso!${RESET}"
echo ""

echo -e "${CYAN}${BOLD}📋 PRÓXIMOS PASSOS:${RESET}"
echo ""
echo -e "${YELLOW}1. TESTAR LOCALMENTE:${RESET}"
echo -e "   ${WHITE}python manage.py runserver${RESET}"
echo -e "   ${CYAN}http://localhost:8000/admin/${RESET}"
echo ""
echo -e "${YELLOW}2. VERIFICAR:${RESET}"
echo -e "   ${WHITE}✓ Botão '📊 Dashboard Financeiro' nas Ações Rápidas${RESET}"
echo -e "   ${WHITE}✓ Botão funciona (sem erros)${RESET}"
echo -e "   ${WHITE}✓ Dashboard carrega${RESET}"
echo -e "   ${WHITE}✓ KPIs aparecem${RESET}"
echo ""
echo -e "${YELLOW}3. SE TUDO OK - DEPLOY:${RESET}"
echo -e "   ${WHITE}git add core/urls.py core/dashboard_views.py core/views_relatorios.py core/templates/admin/index.html${RESET}"
echo -e "   ${WHITE}git commit -m \"feat(dashboard): Dashboard Financeiro completo - DEV_18\"${RESET}"
echo -e "   ${WHITE}git push origin main${RESET}"
echo ""
echo -e "${YELLOW}4. SE NECESSÁRIO REVERTER:${RESET}"
echo -e "   ${WHITE}./$ROLLBACK${RESET}"
echo ""

exit 0
