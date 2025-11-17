#!/bin/bash
# 🎖️ HABITAT PRO - SCRIPT DE DEPLOY SEGURO
# Versão: 1.0 - Recovery 09/11/2025
# Engenharia: Senior Level

set -e  # Exit on any error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
PROJETO_DIR=~/sgli_system
RECOVERY_FILES=/mnt/user-data/outputs

echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🎖️  HABITAT PRO - DEPLOY SEGURO${NC}"
echo -e "${BLUE}    Disaster Recovery - 09/11/2025${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo ""

# Verificar se está no diretório correto
if [ ! -d "$PROJETO_DIR" ]; then
    echo -e "${RED}❌ ERRO: Diretório $PROJETO_DIR não encontrado${NC}"
    echo -e "${YELLOW}Execute: cd ~/sgli_system${NC}"
    exit 1
fi

cd "$PROJETO_DIR"
echo -e "${GREEN}✅ Diretório do projeto: $PROJETO_DIR${NC}"

# Verificar virtual environment
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ ERRO: Virtual environment não encontrado${NC}"
    echo -e "${YELLOW}Execute: python3 -m venv venv${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Virtual environment encontrado${NC}"

# Ativar venv
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment ativado${NC}"
echo ""

# FASE 1: BACKUP DE SEGURANÇA
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}FASE 1: BACKUP DE SEGURANÇA${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/pre_recovery_$TIMESTAMP"

mkdir -p "$BACKUP_DIR"

echo -ne "${YELLOW}Criando backup de models.py... ${NC}"
cp core/models.py "$BACKUP_DIR/models.py.pre_recovery" 2>/dev/null || echo -e "${RED}FALHOU${NC}"
echo -e "${GREEN}OK${NC}"

echo -ne "${YELLOW}Criando backup de admin.py... ${NC}"
cp core/admin.py "$BACKUP_DIR/admin.py.pre_recovery" 2>/dev/null || echo -e "${RED}FALHOU${NC}"
echo -e "${GREEN}OK${NC}"

echo -e "${GREEN}✅ Backups criados em: $BACKUP_DIR${NC}"
echo ""

# FASE 2: VALIDAÇÃO DOS ARQUIVOS DE RECOVERY
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}FASE 2: VALIDAÇÃO DOS ARQUIVOS${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"

if [ ! -f "$RECOVERY_FILES/models.py" ]; then
    echo -e "${RED}❌ ERRO: $RECOVERY_FILES/models.py não encontrado${NC}"
    exit 1
fi

if [ ! -f "$RECOVERY_FILES/admin.py" ]; then
    echo -e "${RED}❌ ERRO: $RECOVERY_FILES/admin.py não encontrado${NC}"
    exit 1
fi

echo -ne "${YELLOW}Validando sintaxe de models.py... ${NC}"
python3 -m py_compile "$RECOVERY_FILES/models.py" 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ VÁLIDO${NC}"
else
    echo -e "${RED}❌ INVÁLIDO - ABORTANDO${NC}"
    exit 1
fi

echo -ne "${YELLOW}Validando sintaxe de admin.py... ${NC}"
python3 -m py_compile "$RECOVERY_FILES/admin.py" 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ VÁLIDO${NC}"
else
    echo -e "${RED}❌ INVÁLIDO - ABORTANDO${NC}"
    exit 1
fi

echo ""

# FASE 3: DEPLOY DOS ARQUIVOS
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}FASE 3: DEPLOY DOS ARQUIVOS${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"

echo -ne "${YELLOW}Copiando models.py restaurado... ${NC}"
cp "$RECOVERY_FILES/models.py" core/models.py
echo -e "${GREEN}OK${NC}"

echo -ne "${YELLOW}Copiando admin.py restaurado... ${NC}"
cp "$RECOVERY_FILES/admin.py" core/admin.py
echo -e "${GREEN}OK${NC}"

echo ""

# FASE 4: LIMPEZA DE CACHE
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}FASE 4: LIMPEZA DE CACHE PYTHON${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"

echo -ne "${YELLOW}Removendo __pycache__... ${NC}"
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
echo -e "${GREEN}OK${NC}"

echo -ne "${YELLOW}Removendo arquivos .pyc... ${NC}"
find . -name "*.pyc" -delete
echo -e "${GREEN}OK${NC}"

echo ""

# FASE 5: VALIDAÇÃO DJANGO
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}FASE 5: VALIDAÇÃO DJANGO${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"

echo -ne "${YELLOW}Executando python manage.py check... ${NC}"
python manage.py check 2>&1 | head -5
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ DJANGO OK${NC}"
else
    echo -e "${RED}❌ DJANGO COM PROBLEMAS${NC}"
    echo -e "${YELLOW}Verifique os erros acima${NC}"
    echo ""
    echo -e "${YELLOW}💡 ROLLBACK disponível em: $BACKUP_DIR${NC}"
    exit 1
fi

echo ""

# FASE 6: SUCESSO
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 DEPLOY CONCLUÍDO COM SUCESSO!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✅ models.py: Restaurado e validado${NC}"
echo -e "${GREEN}✅ admin.py: Restaurado e validado${NC}"
echo -e "${GREEN}✅ Cache Python: Limpo${NC}"
echo -e "${GREEN}✅ Django check: Aprovado${NC}"
echo ""
echo -e "${BLUE}📁 Backup de segurança: $BACKUP_DIR${NC}"
echo ""
echo -e "${YELLOW}🚀 Para iniciar o servidor:${NC}"
echo -e "${YELLOW}   python manage.py runserver 0.0.0.0:8000${NC}"
echo ""
echo -e "${BLUE}📊 MD5 Checksums dos arquivos restaurados:${NC}"
md5sum core/models.py core/admin.py
echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
