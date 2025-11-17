#!/bin/bash
BACKUP_DIR="$(dirname "$0")"
cd ~/sgli_system
echo "Restaurando backup funcional completo..."
cp "$BACKUP_DIR/models.py" core/
cp "$BACKUP_DIR/admin.py" core/
cp "$BACKUP_DIR/dashboard_views.py" core/
cp "$BACKUP_DIR/urls.py" core/
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
echo "✅ Restaurado! Execute: python manage.py runserver"
