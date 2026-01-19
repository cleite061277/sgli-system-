#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "🔧 CORREÇÃO ADICIONAL - BOTÃO EMAIL"
echo "════════════════════════════════════════════════════════════"
echo ""

# Backup
echo "📦 Criando backup..."
cp core/admin.py core/admin.py.backup_email_$(date +%Y%m%d_%H%M%S)
echo "✅ Backup criado!"
echo ""

# Mostrar ANTES
echo "🔍 ANTES (linha 1140):"
sed -n '1140p' core/admin.py
echo ""

# Aplicar correção
echo "🔧 Corrigindo botão Email..."
sed -i 's|href="/comanda/{}/enviar-email/"|href="{}" target="_blank"|g' core/admin.py
echo "✅ Correção aplicada!"
echo ""

# Mostrar DEPOIS
echo "✅ DEPOIS (linha 1140):"
sed -n '1140p' core/admin.py
echo ""

# Validar
python3 -m py_compile core/admin.py
if [ $? -eq 0 ]; then
    echo "✅ Sintaxe válida!"
else
    echo "❌ ERRO! Revertendo..."
    cp core/admin.py.backup_email_* core/admin.py
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ BOTÃO EMAIL CORRIGIDO!"
echo "════════════════════════════════════════════════════════════"
