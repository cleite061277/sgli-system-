#!/bin/bash
# Rollback automático - Dashboard Financeiro
# Gerado: 20251124_231002

echo "⚠️  Iniciando rollback..."

if [ -d "backups_dashboard_20251124_231002" ]; then
    cp backups_dashboard_20251124_231002/core/urls.py core/
    cp backups_dashboard_20251124_231002/core/dashboard_views.py core/
    cp backups_dashboard_20251124_231002/core/views_relatorios.py core/
    rm -f core/templates/admin/index.html
    
    echo "✅ Rollback concluído!"
    echo ""
    echo "Validando..."
    python manage.py check
else
    echo "❌ Backup não encontrado: backups_dashboard_20251124_231002"
    exit 1
fi
