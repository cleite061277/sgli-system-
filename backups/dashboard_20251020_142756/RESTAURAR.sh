#!/bin/bash
echo "════════════════════════════════════════════"
echo "🔄 RESTAURANDO BACKUP..."
echo "════════════════════════════════════════════"
echo ""

# Voltar para o diretório do projeto
cd ~/sgli_system
source venv/bin/activate

# Obter diretório do backup
BACKUP_DIR=$(dirname "$0")

echo "📍 Restaurando de: $BACKUP_DIR"
echo ""

# Restaurar CSS
echo "🎨 Restaurando CSS..."
rm -rf static/admin/css
cp -r "$BACKUP_DIR/css_backup" static/admin/css

# Restaurar templates
echo "📄 Restaurando templates..."
if [ -d "$BACKUP_DIR/templates_backup" ]; then
    rm -rf templates
    cp -r "$BACKUP_DIR/templates_backup" templates
else
    echo "   Removendo templates customizados..."
    rm -rf templates/admin
fi

# Restaurar URLs
echo "🔗 Restaurando URLs..."
cp "$BACKUP_DIR/urls_backup.py" sgli_system/urls.py
[ -f "$BACKUP_DIR/core_urls_backup.py" ] && cp "$BACKUP_DIR/core_urls_backup.py" core/urls.py

# Restaurar views
echo "👁️ Restaurando views..."
cp "$BACKUP_DIR"/views*.py core/ 2>/dev/null || true
cp "$BACKUP_DIR"/admin*.py core/ 2>/dev/null || true

# Remover arquivos que foram criados pela dashboard
echo "🧹 Limpando arquivos novos..."
rm -f core/admin_dashboard.py 2>/dev/null
rm -f core/urls_dashboard.py 2>/dev/null

# Coletar estáticos
echo "📦 Coletando estáticos..."
python manage.py collectstatic --noinput --clear

echo ""
echo "════════════════════════════════════════════"
echo "✅ BACKUP RESTAURADO COM SUCESSO!"
echo "════════════════════════════════════════════"
echo ""
echo "🔄 Reinicie o servidor:"
echo "   python manage.py runserver"
echo ""
