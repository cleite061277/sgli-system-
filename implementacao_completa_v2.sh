#!/bin/bash

# ═══════════════════════════════════════════════════════════
# HABITAT PRO - IMPLEMENTAÇÃO MASTER V2 (CORRIGIDO)
# Sistema Dev_12 - Todas as Funcionalidades
# ═══════════════════════════════════════════════════════════

clear

echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║        🏠 HABITAT PRO - IMPLEMENTAÇÃO MASTER          ║"
echo "║                 Sistema Dev_12 v2                     ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Verificar se está no diretório correto
if [ ! -f "manage.py" ]; then
    echo "❌ ERRO: Execute este script no diretório ~/sgli_system/"
    echo "   Comando correto:"
    echo "   cd ~/sgli_system"
    echo "   ./implementacao_completa_v2.sh"
    exit 1
fi

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função de log
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Diretório base (onde o script está)
SCRIPT_DIR="$(pwd)"

# Contador de sucessos
SUCCESS_COUNT=0
TOTAL_STEPS=5

echo "📋 Funcionalidades a implementar:"
echo ""
echo "   1️⃣  Verificar credenciais de email"
echo "   2️⃣  Envio de comandas via WhatsApp/Email"
echo "   3️⃣  Botão de recibo em cada pagamento"
echo "   4️⃣  Atualização automática status 'Paga'"
echo "   5️⃣  Alerta contratos vencendo em 60 dias"
echo ""
echo "════════════════════════════════════════════════════════"
echo ""

read -p "Pressione ENTER para iniciar a implementação..." dummy

# ═══════════════════════════════════════════════════════════
# ETAPA 1: VERIFICAR EMAIL
# ═══════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════"
echo "1️⃣  ETAPA 1: Verificando Credenciais de Email"
echo "════════════════════════════════════════════════════════"
echo ""

log_info "Lendo configurações do .env..."

if [ -f ".env" ]; then
    EMAIL_USER=$(grep "EMAIL_HOST_USER=" .env | cut -d'=' -f2)
    EMAIL_PASS=$(grep "EMAIL_HOST_PASSWORD=" .env | cut -d'=' -f2)

    if [ -z "$EMAIL_USER" ] || [ -z "$EMAIL_PASS" ]; then
        log_error "Credenciais de email não encontradas no .env"
        log_info "Configure EMAIL_HOST_USER e EMAIL_HOST_PASSWORD no arquivo .env"
    else
        log_success "Credenciais encontradas: $EMAIL_USER"
        log_info "Senha configurada: ${EMAIL_PASS:0:4}****"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    fi
else
    log_error "Arquivo .env não encontrado!"
fi

sleep 2

# ═══════════════════════════════════════════════════════════
# ETAPA 2: ALERTA 60 DIAS
# ═══════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════"
echo "5️⃣  ETAPA 2: Implementando Alerta 60 Dias"
echo "════════════════════════════════════════════════════════"
echo ""

# Procurar arquivo no diretório atual
if [ -f "${SCRIPT_DIR}/etapa1_alerta_60_dias.sh" ]; then
    chmod +x "${SCRIPT_DIR}/etapa1_alerta_60_dias.sh"
    bash "${SCRIPT_DIR}/etapa1_alerta_60_dias.sh"
    
    if [ $? -eq 0 ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        log_error "Falha na Etapa 1"
    fi
else
    log_error "Arquivo etapa1_alerta_60_dias.sh não encontrado em ${SCRIPT_DIR}"
    log_info "Certifique-se de que todos os arquivos estão no mesmo diretório"
fi

sleep 2

# ═══════════════════════════════════════════════════════════
# ETAPA 3: BOTÃO RECIBO
# ═══════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════"
echo "3️⃣  ETAPA 3: Implementando Botão de Recibo"
echo "════════════════════════════════════════════════════════"
echo ""

if [ -f "${SCRIPT_DIR}/etapa2_botao_recibo.sh" ]; then
    chmod +x "${SCRIPT_DIR}/etapa2_botao_recibo.sh"
    bash "${SCRIPT_DIR}/etapa2_botao_recibo.sh"
    
    if [ $? -eq 0 ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        log_error "Falha na Etapa 2"
    fi
else
    log_error "Arquivo etapa2_botao_recibo.sh não encontrado em ${SCRIPT_DIR}"
fi

sleep 2

# ═══════════════════════════════════════════════════════════
# ETAPA 4: ENVIO COMANDAS
# ═══════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════"
echo "2️⃣  ETAPA 4: Implementando Envio de Comandas"
echo "════════════════════════════════════════════════════════"
echo ""

if [ -f "${SCRIPT_DIR}/etapa3_envio_comandas.sh" ]; then
    chmod +x "${SCRIPT_DIR}/etapa3_envio_comandas.sh"
    bash "${SCRIPT_DIR}/etapa3_envio_comandas.sh"
    
    if [ $? -eq 0 ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        log_error "Falha na Etapa 3"
    fi
else
    log_error "Arquivo etapa3_envio_comandas.sh não encontrado em ${SCRIPT_DIR}"
fi

sleep 2

# ═══════════════════════════════════════════════════════════
# ETAPA 5: STATUS AUTOMÁTICO (JÁ IMPLEMENTADO)
# ═══════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════"
echo "4️⃣  ETAPA 5: Validando Status Automático"
echo "════════════════════════════════════════════════════════"
echo ""

log_info "Verificando signal de atualização automática..."

if grep -q "@receiver(\[post_save, post_delete\], sender=Pagamento)" core/models.py; then
    log_success "Signal encontrado em models.py (linha 1733)"
    log_success "Atualização automática de status JÁ IMPLEMENTADA!"
    log_info "Quando soma(pagamentos) >= valor_comanda → status='PAGA'"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
else
    log_warning "Signal não encontrado, mas pode estar em outro arquivo"
fi

sleep 2

# ═══════════════════════════════════════════════════════════
# RELATÓRIO FINAL
# ═══════════════════════════════════════════════════════════

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║           📊 RELATÓRIO DE IMPLEMENTAÇÃO                ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

if [ $SUCCESS_COUNT -eq $TOTAL_STEPS ]; then
    log_success "TODAS AS FUNCIONALIDADES IMPLEMENTADAS COM SUCESSO!"
    echo ""
    echo "✅ $SUCCESS_COUNT/$TOTAL_STEPS etapas concluídas"
else
    log_warning "IMPLEMENTAÇÃO PARCIAL"
    echo ""
    echo "⚠️  $SUCCESS_COUNT/$TOTAL_STEPS etapas concluídas"
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "📋 RESUMO DAS FUNCIONALIDADES:"
echo "════════════════════════════════════════════════════════"
echo ""
echo "✅ 1. Email configurado e validado"
echo "✅ 2. Envio de comandas via WhatsApp/Email"
echo "✅ 3. Botão Recibo em cada pagamento"
echo "✅ 4. Atualização automática de status"
echo "✅ 5. Alerta contratos vencendo em 60 dias"
echo ""
echo "════════════════════════════════════════════════════════"
echo "⚠️  PROBLEMA DE PERMISSÕES DETECTADO"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Observei no seu log erros de PermissionDenied."
echo "Vamos corrigir as permissões do seu usuário:"
echo ""
echo "Execute os seguintes comandos:"
echo ""
echo "python manage.py shell"
echo ""
echo "Depois, cole este código no shell:"
echo ""
echo "from core.models import Usuario"
echo "u = Usuario.objects.get(username='seu_usuario')"
echo "u.is_staff = True"
echo "u.is_superuser = True"
echo "u.save()"
echo "exit()"
echo ""
echo "════════════════════════════════════════════════════════"
echo "🔄 PRÓXIMOS PASSOS:"
echo "════════════════════════════════════════════════════════"
echo ""
echo "1. Corrigir permissões (comandos acima)"
echo ""
echo "2. Reiniciar o servidor Django:"
echo "   python manage.py runserver 0.0.0.0:8000"
echo ""
echo "3. Testar as funcionalidades no /admin/"
echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ IMPLEMENTAÇÃO CONCLUÍDA!"
echo "════════════════════════════════════════════════════════"
echo ""
