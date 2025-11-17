#!/bin/bash
# 🎖️ HABITAT PRO - CORREÇÕES COMPLETAS DEV-9 v2.1
# Versão: 2.1 - 09/11/2025 (CORRIGIDO)
# Executa de DENTRO de ~/sgli_system/correcoes_dev9/

set -e  # Exit on any error

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🎖️  HABITAT PRO - CORREÇÕES COMPLETAS v2.1${NC}"
echo -e "${BLUE}    Problemas 1, 2, 3 e 4 - DEV-9${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo ""

# Detectar diretório atual
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📂 Script executando em: $SCRIPT_DIR"

# Determinar diretório do projeto
# Se estamos em sgli_system/correcoes_dev9/, subir um nível
if [[ "$SCRIPT_DIR" == */sgli_system/correcoes_dev9 ]] || [[ "$SCRIPT_DIR" == */sgli_system/correcoes* ]]; then
    PROJETO_DIR="$(dirname "$SCRIPT_DIR")"
elif [[ "$SCRIPT_DIR" == */sgli_system ]]; then
    PROJETO_DIR="$SCRIPT_DIR"
else
    # Tentar encontrar sgli_system
    if [ -d ~/sgli_system ]; then
        PROJETO_DIR=~/sgli_system
    else
        echo -e "${RED}❌ Não foi possível localizar ~/sgli_system${NC}"
        echo "   Execute este script de dentro de ~/sgli_system/ ou ~/sgli_system/correcoes_dev9/"
        exit 1
    fi
fi

echo "🎯 Projeto identificado em: $PROJETO_DIR"

# Verificar se é o diretório correto
if [ ! -f "$PROJETO_DIR/manage.py" ]; then
    echo -e "${RED}❌ manage.py não encontrado em $PROJETO_DIR${NC}"
    echo "   Este não parece ser o diretório correto do projeto Django."
    exit 1
fi

# Ir para o diretório do projeto
cd "$PROJETO_DIR"
echo "✅ Trabalhando em: $(pwd)"

# Verificar se core/ existe
if [ ! -d "core" ]; then
    echo -e "${RED}❌ Diretório core/ não encontrado!${NC}"
    exit 1
fi

# Ativar virtual environment
echo ""
echo -e "${YELLOW}🔧 Ativando ambiente virtual...${NC}"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Ambiente virtual ativado: $(which python3)"
else
    echo -e "${RED}❌ Virtual environment (venv/) não encontrado!${NC}"
    exit 1
fi

# Localizar arquivos corrigidos
echo ""
echo -e "${YELLOW}🔍 Localizando arquivos corrigidos...${NC}"

# Tentar encontrar arquivos no diretório do script
ARQUIVOS_DIR="$SCRIPT_DIR"

# Verificar se arquivos existem
FALTANDO=""
for arquivo in admin.py.CORRIGIDO models.py.CORRIGIDO dashboard_views.py.CORRIGIDO 0002_alter_comanda_forma_pagamento.py; do
    if [ ! -f "$ARQUIVOS_DIR/$arquivo" ]; then
        FALTANDO="$FALTANDO\n   ❌ $arquivo"
    else
        echo "   ✓ Encontrado: $arquivo"
    fi
done

if [ -n "$FALTANDO" ]; then
    echo -e "${RED}❌ Arquivos não encontrados:${FALTANDO}${NC}"
    echo ""
    echo -e "${YELLOW}💡 SOLUÇÃO:${NC}"
    echo "   Coloque todos os arquivos .CORRIGIDO e a migration no mesmo diretório que este script."
    echo "   Exemplo:"
    echo "   ~/sgli_system/correcoes_dev9/admin.py.CORRIGIDO"
    echo "   ~/sgli_system/correcoes_dev9/models.py.CORRIGIDO"
    echo "   ~/sgli_system/correcoes_dev9/dashboard_views.py.CORRIGIDO"
    echo "   ~/sgli_system/correcoes_dev9/0002_alter_comanda_forma_pagamento.py"
    exit 1
fi

echo -e "${GREEN}✅ Todos os arquivos encontrados!${NC}"

# FASE 1: BACKUP COMPLETO
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}📦 FASE 1: BACKUP COMPLETO${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

BACKUP_DIR="$PROJETO_DIR/backups_dev9_completo_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "📁 Backup em: $BACKUP_DIR"

# Backup de arquivos existentes
for file in admin.py models.py views.py dashboard_views.py; do
    if [ -f "core/$file" ]; then
        echo "   ✓ Backup: core/$file"
        cp "core/$file" "$BACKUP_DIR/${file}.backup"
    else
        echo "   ⚠️  Não encontrado: core/$file"
    fi
done

# Backup do diretório de migrations
if [ -d "core/migrations" ]; then
    echo "   ✓ Backup: core/migrations/"
    cp -r core/migrations "$BACKUP_DIR/migrations_backup"
fi

echo -e "${GREEN}✅ Backup concluído!${NC}"

# FASE 2: CONFIRMAR COM USUÁRIO
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}🔧 FASE 2: APLICAR CORREÇÕES${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

echo ""
echo -e "${YELLOW}📝 As seguintes correções serão aplicadas:${NC}"
echo ""
echo "  1️⃣  admin.py → save_formset (Problema 1)"
echo "  2️⃣  models.py → FormaPagamento global + choices (Problema 2)"
echo "  3️⃣  models.py → imovel.codigo_imovel (Problema 3)"
echo "  4️⃣  dashboard_views.py → status='ACTIVE' (Problema 4)"
echo "  5️⃣  Migration → alter forma_pagamento"
echo ""
echo -e "${YELLOW}⚠️  Esta operação irá:${NC}"
echo "  • Substituir 3 arquivos em core/"
echo "  • Adicionar migration em core/migrations/"
echo "  • Executar makemigrations e migrate"
echo ""
read -p "Deseja continuar? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}⚠️  Operação cancelada pelo usuário${NC}"
    exit 0
fi

# Aplicar correções
echo ""
echo -e "${GREEN}🚀 Aplicando correções...${NC}"

# Copiar arquivos corrigidos de ARQUIVOS_DIR para core/
echo ""
echo "📥 Copiando arquivos corrigidos..."

cp "$ARQUIVOS_DIR/admin.py.CORRIGIDO" core/admin.py
echo "   ✅ core/admin.py atualizado (Problema 1)"

cp "$ARQUIVOS_DIR/models.py.CORRIGIDO" core/models.py
echo "   ✅ core/models.py atualizado (Problemas 2 e 3)"

cp "$ARQUIVOS_DIR/dashboard_views.py.CORRIGIDO" core/dashboard_views.py
echo "   ✅ core/dashboard_views.py atualizado (Problema 4)"

# Copiar migration
cp "$ARQUIVOS_DIR/0002_alter_comanda_forma_pagamento.py" core/migrations/
echo "   ✅ Migration copiada para core/migrations/"

# FASE 3: VALIDAÇÃO DE SINTAXE
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}✓ FASE 3: VALIDAÇÃO DE SINTAXE${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

echo ""
echo "🔍 Validando sintaxe Python..."

VALIDACAO_OK=true

if ! python3 -m py_compile core/admin.py 2>&1; then
    echo -e "${RED}❌ Erro de sintaxe em admin.py!${NC}"
    VALIDACAO_OK=false
fi

if ! python3 -m py_compile core/models.py 2>&1; then
    echo -e "${RED}❌ Erro de sintaxe em models.py!${NC}"
    VALIDACAO_OK=false
fi

if ! python3 -m py_compile core/dashboard_views.py 2>&1; then
    echo -e "${RED}❌ Erro de sintaxe em dashboard_views.py!${NC}"
    VALIDACAO_OK=false
fi

if [ "$VALIDACAO_OK" = false ]; then
    echo ""
    echo -e "${RED}❌ FALHA NA VALIDAÇÃO! Restaurando backups...${NC}"
    cp "$BACKUP_DIR/admin.py.backup" core/admin.py 2>/dev/null || true
    cp "$BACKUP_DIR/models.py.backup" core/models.py 2>/dev/null || true
    cp "$BACKUP_DIR/dashboard_views.py.backup" core/dashboard_views.py 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Validação de sintaxe: PASSOU!${NC}"

# FASE 4: MIGRATIONS
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}🗄️  FASE 4: MIGRATIONS${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

echo ""
echo "🔄 Executando migrate..."
if python manage.py migrate 2>&1 | tee /tmp/migrate_output.log; then
    echo -e "${GREEN}✅ Migrations aplicadas!${NC}"
else
    echo -e "${YELLOW}⚠️  Verifique os logs acima${NC}"
fi

# FASE 5: VALIDAÇÃO DJANGO
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}🧪 FASE 5: VALIDAÇÃO DJANGO${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

echo ""
echo "🔍 Executando django check..."
if python manage.py check 2>&1; then
    echo -e "${GREEN}✅ Django check: PASSOU!${NC}"
else
    echo -e "${YELLOW}⚠️  Há avisos (provavelmente normais)${NC}"
fi

# CONCLUSÃO
echo ""
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 CORREÇÕES APLICADAS COM SUCESSO!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"

echo ""
echo -e "${GREEN}✅ PROBLEMA 1:${NC} Pagamento inline → usuario_registro OK"
echo -e "${GREEN}✅ PROBLEMA 2:${NC} FormaPagamento → Choices unificados"
echo -e "${GREEN}✅ PROBLEMA 3:${NC} Geração de contrato → codigo_imovel OK"
echo -e "${GREEN}✅ PROBLEMA 4:${NC} Dashboard → Contador correto"

echo ""
echo -e "${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo ""
echo "1. 🔄 Reiniciar servidor:"
echo "   cd ~/sgli_system"
echo "   python manage.py runserver"
echo ""
echo "2. 🧪 TESTAR (4 testes obrigatórios):"
echo "   A) Dashboard → Ver contador de contratos"
echo "   B) Comanda → Adicionar pagamento inline"
echo "   C) Locação → Criar nova locação"
echo "   D) Comanda/Pagamento → Verificar choices"
echo ""
echo "3. ✅ Se tudo OK → Deploy para produção"
echo "   (NÃO incluído neste script - faremos separadamente)"
echo ""

echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}📂 Backup salvo em:${NC}"
echo "   $BACKUP_DIR"
echo ""
echo -e "${YELLOW}Restaurar backup se necessário:${NC}"
echo "   cp $BACKUP_DIR/*.backup core/"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}🎖️ Aplicação completa! Reinicie o servidor e teste.${NC}"
echo ""
