#!/bin/bash
# Script de Restauração - Estado Funcional Parcial

BACKUP_DIR="$(dirname "$0")"
PROJETO_DIR="$HOME/sgli_system"

echo "════════════════════════════════════════════"
echo "🔄 RESTAURANDO BACKUP"
echo "════════════════════════════════════════════"
echo ""
echo "Origem: $BACKUP_DIR"
echo "Destino: $PROJETO_DIR"
echo ""
read -p "Confirma restauração? (s/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Cancelado."
    exit 1
fi

cd "$PROJETO_DIR"

# Restaurar arquivos
cp "$BACKUP_DIR/models.py.backup" core/models.py
cp "$BACKUP_DIR/admin.py.backup" core/admin.py
cp "$BACKUP_DIR/dashboard_views.py.backup" core/dashboard_views.py
cp "$BACKUP_DIR/urls.py.backup" core/urls.py
cp "$BACKUP_DIR/settings.py.backup" sgli_project/settings.py

# Limpar cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

echo ""
echo "✅ Restauração concluída!"
echo "Inicie o servidor: python manage.py runserver"
