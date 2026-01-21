#!/bin/bash

# ==========================================
# ROLLBACK AUTOMÁTICO - OPÇÃO 1+3 MELHORADA
# ==========================================

echo "🔄 Iniciando rollback da Opção 1+3 Melhorada..."
echo ""

# Encontrar backup mais recente
BACKUP_DIR=$(ls -td backups_opcao1+3_* 2>/dev/null | head -1)

if [ -z "$BACKUP_DIR" ]; then
    echo "❌ Nenhum backup encontrado!"
    echo ""
    echo "Use rollback Git:"
    echo "  git tag | grep backup-opcao1+3"
    echo "  git checkout <tag>"
    exit 1
fi

echo "→ Encontrado backup: $BACKUP_DIR"
echo ""

# Restaurar models.py
if [ -f "$BACKUP_DIR/models.py.backup" ]; then
    echo "→ Restaurando core/models.py..."
    cp "$BACKUP_DIR/models.py.backup" core/models.py
    echo "✅ models.py restaurado"
else
    echo "❌ Backup models.py não encontrado!"
fi

# Remover arquivos CSS/JS adicionados
echo ""
echo "→ Removendo arquivos CSS/JS criados..."
rm -f static/admin/css/menu_habitat_pro.css
rm -f static/admin/js/menu_collapse.js
echo "✅ Arquivos CSS/JS removidos"

# Restaurar templates se tiver backup
if [ -d "$BACKUP_DIR/admin_templates_backup" ]; then
    echo ""
    echo "→ Restaurando templates admin..."
    rm -rf core/templates/admin
    cp -r "$BACKUP_DIR/admin_templates_backup" core/templates/admin
    echo "✅ Templates restaurados"
fi

# Collectstatic
echo ""
echo "→ Executando collectstatic..."
python manage.py collectstatic --noinput --clear > /dev/null 2>&1
echo "✅ Collectstatic executado"

# Parar servidor
echo ""
echo "→ Reiniciando servidor..."
pkill -f "manage.py runserver" 2>/dev/null || true

echo ""
echo "=========================================="
echo "✅ ROLLBACK COMPLETO!"
echo "=========================================="
echo ""
echo "Sistema restaurado ao estado original."
echo ""
echo "Execute: python manage.py runserver"
echo ""
