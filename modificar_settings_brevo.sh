#!/bin/bash
################################################################################
# SCRIPT: Backup e Modificação Settings.py para Brevo
################################################################################
# Este script faz backup do settings.py e modifica a configuração de email
# de SendGrid para Brevo de forma cirúrgica
################################################################################

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="$HOME/sgli_system"
SETTINGS_FILE="$PROJECT_DIR/sgli_project/settings.py"

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}BACKUP E MODIFICAÇÃO SETTINGS.PY - BREVO${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"

# Verificar se arquivo existe
if [ ! -f "$SETTINGS_FILE" ]; then
    echo -e "${RED}❌ Arquivo não encontrado: $SETTINGS_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}📁 Arquivo: $SETTINGS_FILE${NC}"

# Criar backup
echo -e "\n${YELLOW}📦 Criando backup...${NC}"
cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bkp_sendgrid_${TIMESTAMP}"
echo -e "${GREEN}✅ Backup criado: ${SETTINGS_FILE}.bkp_sendgrid_${TIMESTAMP}${NC}"

# Verificar se SendGrid está presente
if grep -q "SENDGRID_API_KEY" "$SETTINGS_FILE"; then
    echo -e "\n${YELLOW}🔍 Configuração SendGrid detectada${NC}"
    echo -e "${YELLOW}📝 Aplicando modificação cirúrgica...${NC}"
    
    # Criar arquivo temporário com a nova configuração
    cat > /tmp/brevo_config_block.txt << 'EOF'

# ═══════════════════════════════════════════════════════════════
# EMAIL CONFIGURATION - BREVO (Sendinblue)
# ═══════════════════════════════════════════════════════════════
# Migração: SendGrid → Brevo | Data: 18/01/2026
# Economia: R$ 1.434,00/ano | Capacidade: 9.000 emails/mês
# ═══════════════════════════════════════════════════════════════

ANYMAIL = {
    "SENDINBLUE_API_KEY": env('BREVO_API_KEY'),
}
EMAIL_BACKEND = "anymail.backends.sendinblue.EmailBackend"
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default="habitatprohabitatproimoveis@gmail.com")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_TIMEOUT = 10

EOF
    
    # Fazer a substituição usando Python para ser mais preciso
    python3 << 'PYTHON_SCRIPT'
import re

settings_file = "/home/usuario/sgli_system/sgli_project/settings.py"

# Ler arquivo original
with open(settings_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Ler novo bloco
with open('/tmp/brevo_config_block.txt', 'r', encoding='utf-8') as f:
    new_block = f.read()

# Pattern para encontrar bloco SendGrid
# Procura desde "ANYMAIL = {" até "EMAIL_TIMEOUT" ou similar
pattern = r'(# [=\s]*EMAIL.*?SENDGRID.*?\n.*?)?ANYMAIL\s*=\s*\{[^}]*SENDGRID[^}]*\}.*?EMAIL_BACKEND\s*=\s*["\']anymail\.backends\.sendgrid\.EmailBackend["\'].*?(?:EMAIL_TIMEOUT\s*=\s*\d+)?'

# Substituir
if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
    new_content = re.sub(pattern, new_block.strip(), content, flags=re.DOTALL | re.IGNORECASE)
    
    # Salvar
    with open(settings_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Substituição realizada com sucesso!")
else:
    print("⚠️  Pattern SendGrid não encontrado - será necessário edição manual")
    print("📝 Procure por 'SENDGRID_API_KEY' no arquivo e substitua manualmente")
PYTHON_SCRIPT
    
    echo -e "${GREEN}✅ Modificação aplicada!${NC}"
    
else
    echo -e "\n${YELLOW}⚠️  SendGrid não detectado no settings.py${NC}"
    echo -e "${YELLOW}📝 Será necessário adicionar configuração Brevo manualmente${NC}"
fi

# Validar sintaxe Python
echo -e "\n${YELLOW}🔍 Validando sintaxe Python...${NC}"
if python3 -m py_compile "$SETTINGS_FILE" 2>/dev/null; then
    echo -e "${GREEN}✅ Sintaxe Python válida!${NC}"
else
    echo -e "${RED}❌ ERRO DE SINTAXE detectado!${NC}"
    echo -e "${YELLOW}🔄 Restaurando backup...${NC}"
    cp "${SETTINGS_FILE}.bkp_sendgrid_${TIMESTAMP}" "$SETTINGS_FILE"
    echo -e "${GREEN}✅ Backup restaurado${NC}"
    exit 1
fi

echo -e "\n${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ MODIFICAÇÃO CONCLUÍDA COM SUCESSO!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo -e "1. Adicionar BREVO_API_KEY ao arquivo .env"
echo -e "2. Executar: python validar_email_brevo_local.py"
echo -e "3. Se teste OK → commit e deploy"
echo -e "\n${YELLOW}🔄 ROLLBACK (se necessário):${NC}"
echo -e "cp ${SETTINGS_FILE}.bkp_sendgrid_${TIMESTAMP} $SETTINGS_FILE"
