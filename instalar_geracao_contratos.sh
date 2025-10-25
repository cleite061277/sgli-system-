#!/bin/bash

echo "🔧 Instalando geração de contratos..."
echo ""

# 1. Criar admin_views.py
echo "📝 Criando admin_views.py..."
cat > core/admin_views.py << 'EOF'
"""
Views auxiliares para download de contratos
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from .models import Locacao


@staff_member_required
def download_contrato_pdf(request, pk):
    from .admin import gerar_contrato_pdf
    locacao = get_object_or_404(Locacao, pk=pk)
    return gerar_contrato_pdf(locacao)


@staff_member_required
def download_contrato_docx(request, pk):
    from .admin import gerar_contrato_docx
    locacao = get_object_or_404(Locacao, pk=pk)
    return gerar_contrato_docx(locacao)
EOF

echo "✅ admin_views.py criado"
echo ""

# 2. Adicionar URLs
echo "📝 Adicionando URLs..."

# Verificar se já existem
if ! grep -q "admin_views" core/urls.py; then
    # Adicionar import
    sed -i '/from django.urls import path/a from . import admin_views' core/urls.py
    
    # Adicionar URLs antes do último ]
    sed -i '$i\    # Download de contratos' core/urls.py
    sed -i "\$i\    path('admin/locacao/<uuid:pk>/contrato/pdf/', admin_views.download_contrato_pdf, name='admin_gerar_contrato_pdf')," core/urls.py
    sed -i "\$i\    path('admin/locacao/<uuid:pk>/contrato/docx/', admin_views.download_contrato_docx, name='admin_gerar_contrato_docx')," core/urls.py
    
    echo "✅ URLs adicionadas"
else
    echo "ℹ️  URLs já existem"
fi

echo ""
echo "=" * 70
echo "✅ Instalação concluída!"
echo "=" * 70
echo ""
echo "📋 Próximos passos MANUAIS:"
echo "   1. Editar core/admin.py"
echo "   2. Adicionar as funções gerar_contrato_pdf e gerar_contrato_docx"
echo "   3. Atualizar a classe LocacaoAdmin"
echo "   4. Reiniciar servidor"
echo ""

