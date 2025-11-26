#!/bin/bash
################################################################################
#                                                                              #
#  🎯 INSTALADOR MASTER - DASHBOARD FINANCEIRO HABITAT PRO                     #
#                                                                              #
#  Instala o Dashboard Financeiro com backup, validação e rollback automático #
#                                                                              #
################################################################################

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
BOLD='\033[1m'
RESET='\033[0m'

# Variáveis globais
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups_dashboard_${TIMESTAMP}"
LOG_FILE="instalacao_dashboard_${TIMESTAMP}.log"
ERRO_ENCONTRADO=0
ETAPA_ATUAL=0
TOTAL_ETAPAS=10

################################################################################
# FUNÇÕES DE UTILITÁRIO
################################################################################

print_header() {
    echo ""
    echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════════${RESET}"
    echo -e "${BLUE}${BOLD}  $1${RESET}"
    echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════════${RESET}"
    echo ""
}

print_section() {
    ETAPA_ATUAL=$((ETAPA_ATUAL + 1))
    echo ""
    echo -e "${CYAN}${BOLD}───────────────────────────────────────────────────────────────────${RESET}"
    echo -e "${CYAN}${BOLD}[${ETAPA_ATUAL}/${TOTAL_ETAPAS}] $1${RESET}"
    echo -e "${CYAN}${BOLD}───────────────────────────────────────────────────────────────────${RESET}"
    echo "" | tee -a "$LOG_FILE"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ETAPA ${ETAPA_ATUAL}: $1" >> "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}✅ $1${RESET}" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}❌ ERRO: $1${RESET}" | tee -a "$LOG_FILE"
    ERRO_ENCONTRADO=1
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${RESET}" | tee -a "$LOG_FILE"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${RESET}" | tee -a "$LOG_FILE"
}

print_progress() {
    echo -e "${MAGENTA}⏳ $1${RESET}"
}

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Função para sair em caso de erro
exit_on_error() {
    if [ $ERRO_ENCONTRADO -eq 1 ]; then
        echo ""
        print_error "Instalação abortada devido a erros"
        print_info "Verifique o log: $LOG_FILE"
        
        if [ -d "$BACKUP_DIR" ]; then
            print_warning "Backups disponíveis em: $BACKUP_DIR"
            print_info "Para reverter: ./rollback_dashboard_${TIMESTAMP}.sh"
        fi
        
        exit 1
    fi
}

################################################################################
# ETAPA 1: VERIFICAÇÃO DE AMBIENTE
################################################################################

verificar_ambiente() {
    print_section "VERIFICAÇÃO DE AMBIENTE"
    
    # Verificar se está no diretório correto
    print_progress "Verificando diretório do projeto..."
    if [ ! -f "manage.py" ]; then
        print_error "Arquivo manage.py não encontrado!"
        print_info "Execute: cd ~/sgli_system"
        exit_on_error
    fi
    print_success "Diretório correto: $(pwd)"
    
    # Verificar Python
    print_progress "Verificando Python..."
    if ! command_exists python; then
        print_error "Python não encontrado!"
        exit_on_error
    fi
    PYTHON_VERSION=$(python --version 2>&1)
    print_success "Python encontrado: $PYTHON_VERSION"
    
    # Verificar ambiente virtual
    print_progress "Verificando ambiente virtual..."
    if [ -z "$VIRTUAL_ENV" ]; then
        print_warning "Ambiente virtual não ativado"
        print_info "Tentando ativar: source venv/bin/activate"
        
        if [ -d "venv" ]; then
            source venv/bin/activate
            if [ -z "$VIRTUAL_ENV" ]; then
                print_error "Falha ao ativar ambiente virtual"
                exit_on_error
            fi
            print_success "Ambiente virtual ativado"
        else
            print_warning "Ambiente virtual não encontrado, continuando sem ele"
        fi
    else
        print_success "Ambiente virtual ativo: $VIRTUAL_ENV"
    fi
    
    # Verificar Django
    print_progress "Verificando Django..."
    DJANGO_VERSION=$(python -c "import django; print(django.get_version())" 2>&1)
    if [ $? -ne 0 ]; then
        print_error "Django não encontrado ou erro ao importar"
        exit_on_error
    fi
    print_success "Django encontrado: $DJANGO_VERSION"
}

################################################################################
# ETAPA 2: VERIFICAÇÃO DE ARQUIVOS
################################################################################

verificar_arquivos() {
    print_section "VERIFICAÇÃO DE ARQUIVOS NECESSÁRIOS"
    
    ARQUIVOS_NECESSARIOS=("urls.py" "dashboard_views.py" "index.html")
    
    for arquivo in "${ARQUIVOS_NECESSARIOS[@]}"; do
        print_progress "Verificando: $arquivo"
        
        if [ ! -f "$arquivo" ]; then
            print_error "Arquivo não encontrado: $arquivo"
            print_info "Certifique-se de ter baixado e copiado todos os arquivos"
            print_info "Comando: cp ~/Downloads/*.py ~/Downloads/index.html ."
            exit_on_error
        fi
        
        # Verificar tamanho do arquivo
        TAMANHO=$(stat -f%z "$arquivo" 2>/dev/null || stat -c%s "$arquivo" 2>/dev/null)
        if [ "$TAMANHO" -lt 100 ]; then
            print_error "Arquivo muito pequeno ou vazio: $arquivo"
            exit_on_error
        fi
        
        print_success "$arquivo OK ($TAMANHO bytes)"
    done
}

################################################################################
# ETAPA 3: CRIAÇÃO DE BACKUP
################################################################################

criar_backup() {
    print_section "CRIAÇÃO DE BACKUP"
    
    print_progress "Criando diretório de backup..."
    mkdir -p "$BACKUP_DIR"
    print_success "Diretório criado: $BACKUP_DIR"
    
    # Arquivos a fazer backup
    ARQUIVOS_BACKUP=(
        "core/urls.py"
        "core/dashboard_views.py"
        "core/templates/admin/index.html"
    )
    
    for arquivo in "${ARQUIVOS_BACKUP[@]}"; do
        if [ -f "$arquivo" ]; then
            print_progress "Backup: $arquivo"
            
            # Criar subdiretórios necessários
            BACKUP_PATH="$BACKUP_DIR/$arquivo"
            mkdir -p "$(dirname "$BACKUP_PATH")"
            
            # Copiar arquivo
            cp "$arquivo" "$BACKUP_PATH"
            if [ $? -eq 0 ]; then
                print_success "✓ $arquivo → $BACKUP_PATH"
            else
                print_error "Falha ao criar backup de $arquivo"
                exit_on_error
            fi
        else
            print_info "Arquivo não existe (será criado): $arquivo"
        fi
    done
}

################################################################################
# ETAPA 4: VALIDAÇÃO DE SINTAXE
################################################################################

validar_sintaxe() {
    print_section "VALIDAÇÃO DE SINTAXE PYTHON"
    
    ARQUIVOS_PYTHON=("urls.py" "dashboard_views.py")
    
    for arquivo in "${ARQUIVOS_PYTHON[@]}"; do
        print_progress "Validando sintaxe: $arquivo"
        
        python -m py_compile "$arquivo" 2>> "$LOG_FILE"
        if [ $? -ne 0 ]; then
            print_error "Erro de sintaxe em $arquivo"
            print_info "Verifique o arquivo e tente novamente"
            cat "$LOG_FILE" | tail -n 10
            exit_on_error
        fi
        
        print_success "✓ $arquivo (sintaxe OK)"
    done
}

################################################################################
# ETAPA 5: INSTALAÇÃO DE ARQUIVOS
################################################################################

instalar_arquivos() {
    print_section "INSTALAÇÃO DE ARQUIVOS"
    
    # 1. Instalar urls.py
    print_progress "Instalando core/urls.py..."
    cp urls.py core/urls.py
    if [ $? -eq 0 ]; then
        print_success "✓ core/urls.py atualizado"
    else
        print_error "Falha ao copiar urls.py"
        exit_on_error
    fi
    
    # 2. Instalar dashboard_views.py
    print_progress "Instalando core/dashboard_views.py..."
    cp dashboard_views.py core/dashboard_views.py
    if [ $? -eq 0 ]; then
        print_success "✓ core/dashboard_views.py atualizado"
    else
        print_error "Falha ao copiar dashboard_views.py"
        exit_on_error
    fi
    
    # 3. Instalar template
    print_progress "Instalando core/templates/admin/index.html..."
    mkdir -p core/templates/admin
    cp index.html core/templates/admin/index.html
    if [ $? -eq 0 ]; then
        print_success "✓ core/templates/admin/index.html criado"
    else
        print_error "Falha ao copiar index.html"
        exit_on_error
    fi
}

################################################################################
# ETAPA 6: VALIDAÇÃO DJANGO
################################################################################

validar_django() {
    print_section "VALIDAÇÃO DJANGO"
    
    print_progress "Executando: python manage.py check"
    
    python manage.py check > check_output.tmp 2>&1
    RESULTADO=$?
    
    if [ $RESULTADO -eq 0 ]; then
        print_success "✓ Sistema Django validado sem erros"
        cat check_output.tmp >> "$LOG_FILE"
    else
        print_error "Django check encontrou erros:"
        cat check_output.tmp | tee -a "$LOG_FILE"
        rm -f check_output.tmp
        exit_on_error
    fi
    
    rm -f check_output.tmp
}

################################################################################
# ETAPA 7: VERIFICAÇÃO DE URLS
################################################################################

verificar_urls() {
    print_section "VERIFICAÇÃO DE ROTAS"
    
    print_progress "Verificando rotas do dashboard..."
    
    # Tentar listar URLs (se show_urls existir)
    python manage.py show_urls 2>/dev/null | grep -i dashboard >> "$LOG_FILE"
    
    # Verificar se as rotas existem no arquivo
    if grep -q "dashboard_financeiro" core/urls.py; then
        print_success "✓ Rotas do dashboard encontradas em urls.py"
    else
        print_error "Rotas do dashboard não encontradas"
        exit_on_error
    fi
}

################################################################################
# ETAPA 8: CRIAÇÃO DE SCRIPT DE ROLLBACK
################################################################################

criar_rollback() {
    print_section "CRIAÇÃO DE SCRIPT DE ROLLBACK"
    
    ROLLBACK_SCRIPT="rollback_dashboard_${TIMESTAMP}.sh"
    
    print_progress "Gerando script: $ROLLBACK_SCRIPT"
    
    cat > "$ROLLBACK_SCRIPT" << 'EOF'
#!/bin/bash
# Script de Rollback - Dashboard Financeiro
# Gerado automaticamente

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RESET='\033[0m'

echo ""
echo -e "${YELLOW}⚠️  INICIANDO ROLLBACK DO DASHBOARD FINANCEIRO${RESET}"
echo ""

EOF
    
    echo "BACKUP_DIR=\"$BACKUP_DIR\"" >> "$ROLLBACK_SCRIPT"
    echo "TIMESTAMP=\"$TIMESTAMP\"" >> "$ROLLBACK_SCRIPT"
    echo "" >> "$ROLLBACK_SCRIPT"
    
    cat >> "$ROLLBACK_SCRIPT" << 'EOF'

if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}❌ Diretório de backup não encontrado: $BACKUP_DIR${RESET}"
    exit 1
fi

# Restaurar arquivos
echo -e "${YELLOW}Restaurando arquivos do backup...${RESET}"

if [ -f "$BACKUP_DIR/core/urls.py" ]; then
    cp "$BACKUP_DIR/core/urls.py" core/urls.py
    echo -e "${GREEN}✓ core/urls.py restaurado${RESET}"
fi

if [ -f "$BACKUP_DIR/core/dashboard_views.py" ]; then
    cp "$BACKUP_DIR/core/dashboard_views.py" core/dashboard_views.py
    echo -e "${GREEN}✓ core/dashboard_views.py restaurado${RESET}"
fi

if [ -f "$BACKUP_DIR/core/templates/admin/index.html" ]; then
    rm -f core/templates/admin/index.html
    echo -e "${GREEN}✓ core/templates/admin/index.html removido${RESET}"
fi

echo ""
echo -e "${GREEN}✅ ROLLBACK CONCLUÍDO!${RESET}"
echo ""
echo -e "${YELLOW}Validando sistema...${RESET}"
python manage.py check

echo ""
echo -e "${YELLOW}Para remover arquivos de backup:${RESET}"
echo -e "  rm -rf $BACKUP_DIR"
echo ""

EOF
    
    chmod +x "$ROLLBACK_SCRIPT"
    print_success "✓ Script de rollback criado: $ROLLBACK_SCRIPT"
}

################################################################################
# ETAPA 9: TESTE DE IMPORTAÇÃO
################################################################################

testar_importacao() {
    print_section "TESTE DE IMPORTAÇÃO"
    
    print_progress "Testando importação dos módulos..."
    
    python << 'PYEOF' >> "$LOG_FILE" 2>&1
import sys
sys.path.insert(0, 'core')

try:
    from dashboard_views import admin_index
    print("✓ dashboard_views.admin_index OK")
except Exception as e:
    print(f"✗ Erro ao importar dashboard_views: {e}")
    sys.exit(1)

try:
    from views_relatorios import dashboard_financeiro
    print("✓ views_relatorios.dashboard_financeiro OK")
except Exception as e:
    print(f"✗ Erro ao importar views_relatorios: {e}")
    sys.exit(1)

print("✓ Todos os módulos importados com sucesso")
PYEOF
    
    if [ $? -eq 0 ]; then
        print_success "✓ Módulos importados com sucesso"
    else
        print_error "Erro ao importar módulos"
        print_info "Verifique o log: $LOG_FILE"
        exit_on_error
    fi
}

################################################################################
# ETAPA 10: RELATÓRIO FINAL
################################################################################

gerar_relatorio() {
    print_section "RELATÓRIO DE INSTALAÇÃO"
    
    echo ""
    echo -e "${BOLD}📋 ARQUIVOS MODIFICADOS:${RESET}"
    echo "  • core/urls.py"
    echo "  • core/dashboard_views.py"
    echo "  • core/templates/admin/index.html (criado)"
    
    echo ""
    echo -e "${BOLD}📂 BACKUP CRIADO:${RESET}"
    echo "  📁 $BACKUP_DIR"
    
    echo ""
    echo -e "${BOLD}📄 LOG COMPLETO:${RESET}"
    echo "  📄 $LOG_FILE"
    
    echo ""
    echo -e "${BOLD}🔄 SCRIPT DE ROLLBACK:${RESET}"
    echo "  📜 ./$ROLLBACK_SCRIPT"
    
    echo ""
    echo -e "${BOLD}⏱️  TIMESTAMP:${RESET}"
    echo "  🕐 $TIMESTAMP"
}

################################################################################
# FUNÇÃO PRINCIPAL
################################################################################

main() {
    clear
    
    print_header "🎯 INSTALADOR MASTER - DASHBOARD FINANCEIRO HABITAT PRO"
    
    echo -e "${CYAN}Iniciando instalação em: $(date +'%Y-%m-%d %H:%M:%S')${RESET}"
    echo -e "${CYAN}Log: $LOG_FILE${RESET}"
    echo ""
    
    # Executar todas as etapas
    verificar_ambiente
    exit_on_error
    
    verificar_arquivos
    exit_on_error
    
    criar_backup
    exit_on_error
    
    validar_sintaxe
    exit_on_error
    
    instalar_arquivos
    exit_on_error
    
    validar_django
    exit_on_error
    
    verificar_urls
    exit_on_error
    
    criar_rollback
    exit_on_error
    
    testar_importacao
    exit_on_error
    
    gerar_relatorio
    
    # Sucesso!
    echo ""
    print_header "🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
    
    echo ""
    echo -e "${GREEN}${BOLD}✅ Dashboard Financeiro instalado e pronto para uso!${RESET}"
    echo ""
    
    echo -e "${CYAN}${BOLD}📋 PRÓXIMOS PASSOS:${RESET}"
    echo ""
    echo -e "${YELLOW}1. TESTAR LOCALMENTE:${RESET}"
    echo -e "   ${WHITE}python manage.py runserver${RESET}"
    echo -e "   ${CYAN}Acessar: http://localhost:8000/admin/${RESET}"
    echo -e "   ${CYAN}Verificar: Botão '📊 Dashboard Financeiro' nas Ações Rápidas${RESET}"
    echo ""
    
    echo -e "${YELLOW}2. DEPLOY PARA PRODUÇÃO:${RESET}"
    echo -e "   ${WHITE}git add core/urls.py core/dashboard_views.py core/templates/admin/index.html${RESET}"
    echo -e "   ${WHITE}git commit -m \"feat(dashboard): Dashboard nas Ações Rápidas - DEV_18\"${RESET}"
    echo -e "   ${WHITE}git push origin main${RESET}"
    echo ""
    
    echo -e "${YELLOW}3. SE ALGO DER ERRADO (REVERTER):${RESET}"
    echo -e "   ${WHITE}./$ROLLBACK_SCRIPT${RESET}"
    echo ""
    
    echo -e "${CYAN}Log completo salvo em: ${WHITE}$LOG_FILE${RESET}"
    echo ""
    
    exit 0
}

################################################################################
# TRATAMENTO DE SINAIS
################################################################################

trap 'echo -e "\n\n${RED}❌ Instalação cancelada pelo usuário${RESET}\n"; exit 1' INT TERM

################################################################################
# EXECUTAR
################################################################################

main "$@"
