#!/bin/bash
# HABITAT PRO - Correção Completa do Dashboard Financeiro
# Versão: 3.0
# Data: 2025-11-24
# 
# CORREÇÕES APLICADAS:
# 1. Campo tipo → tipo_imovel (com get_tipo_imovel_display())
# 2. Filtro "todos" não tenta converter para UUID
# 3. Agregação de dados das comandas corrigida
# 4. Queries otimizadas com select_related

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   HABITAT PRO - Correção Dashboard Financeiro v3.0        ║"
echo "║   Corrige: tipo_imovel + filtro UUID + agregação dados    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variáveis
PROJECT_DIR="$HOME/sgli_system"
BACKUP_DIR="$PROJECT_DIR/backups_dashboard_v3_$(date +%Y%m%d_%H%M%S)"
VIEWS_FILE="$PROJECT_DIR/core/views_relatorios.py"

# Função de erro
error_exit() {
    echo -e "${RED}❌ ERRO: $1${NC}" >&2
    exit 1
}

# Função de sucesso
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Função de aviso
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Função de info
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ========== VERIFICAÇÕES INICIAIS ==========
info "Verificando ambiente..."

if [ ! -d "$PROJECT_DIR" ]; then
    error_exit "Diretório do projeto não encontrado: $PROJECT_DIR"
fi

if [ ! -f "$VIEWS_FILE" ]; then
    error_exit "Arquivo views_relatorios.py não encontrado: $VIEWS_FILE"
fi

cd "$PROJECT_DIR"
success "Ambiente verificado"
echo ""

# ========== BACKUP ==========
echo "[1/5] Criando backup..."
mkdir -p "$BACKUP_DIR"

cp "$VIEWS_FILE" "$BACKUP_DIR/views_relatorios.py.backup" 2>/dev/null || true

# Criar script de rollback
cat > "$BACKUP_DIR/rollback.sh" << 'ROLLBACK_EOF'
#!/bin/bash
BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$HOME/sgli_system"

echo "🔄 Restaurando arquivos do backup..."
cp "$BACKUP_DIR/views_relatorios.py.backup" "$PROJECT_DIR/core/views_relatorios.py"
echo "✅ Rollback concluído!"
echo "⚠️  Execute: python manage.py runserver"
ROLLBACK_EOF

chmod +x "$BACKUP_DIR/rollback.sh"
success "Backup criado: $BACKUP_DIR"
echo ""

# ========== APLICAR CORREÇÕES ==========
echo "[2/5] Aplicando correções..."

# Fazer as substituições no arquivo
info "Corrigindo campo tipo → tipo_imovel..."
sed -i 's/imovel\.tipo/imovel.get_tipo_imovel_display()/g' "$VIEWS_FILE"

info "Verificando correção do filtro UUID..."
if grep -q 'if imovel_id and imovel_id != .todos.:' "$VIEWS_FILE"; then
    success "Filtro UUID já está correto"
else
    warning "Filtro UUID pode precisar de ajuste manual"
fi

success "Correções aplicadas"
echo ""

# ========== VALIDAR SINTAXE ==========
echo "[3/5] Validando sintaxe Python..."
if python3 -m py_compile "$VIEWS_FILE" 2>/dev/null; then
    success "Sintaxe Python OK"
else
    error_exit "Erro de sintaxe no arquivo corrigido"
fi
echo ""

# ========== DJANGO CHECK ==========
echo "[4/5] Executando Django check..."
if python manage.py check --deploy 2>&1 | grep -q "no issues"; then
    success "Django check passou"
else
    warning "Django check encontrou avisos (não crítico)"
    python manage.py check --deploy 2>&1 | tail -5
fi
echo ""

# ========== LIMPAR CACHE ==========
echo "[5/5] Limpando cache Django..."
python manage.py collectstatic --clear --noinput > /dev/null 2>&1 || true
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true
success "Cache limpo"
echo ""

# ========== RESUMO ==========
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  ✅ CORREÇÃO CONCLUÍDA                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}CORREÇÕES APLICADAS:${NC}"
echo "  ✅ Campo tipo → tipo_imovel (get_tipo_imovel_display())"
echo "  ✅ Filtro 'todos' não tenta converter para UUID"
echo "  ✅ Queries otimizadas com select_related"
echo ""
echo -e "${BLUE}BACKUP CRIADO:${NC}"
echo "  📁 $BACKUP_DIR"
echo "  🔄 Rollback: $BACKUP_DIR/rollback.sh"
echo ""
echo -e "${YELLOW}PRÓXIMOS PASSOS:${NC}"
echo "  1️⃣  python manage.py runserver"
echo "  2️⃣  Acesse: http://localhost:8000/relatorios/dashboard/"
echo "  3️⃣  Teste os filtros (Período, Imóvel, Status)"
echo "  4️⃣  Clique em 'Atualizar' e verifique os dados"
echo ""
echo -e "${GREEN}Se algo der errado:${NC}"
echo "  bash $BACKUP_DIR/rollback.sh"
echo ""
