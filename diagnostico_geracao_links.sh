#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "🔍 DIAGNÓSTICO - GERAÇÃO DE LINKS"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "1️⃣ BUSCAR ONDE gerar_token_comanda É CHAMADO:"
echo "───────────────────────────────────────────────────────────────"
grep -rn "gerar_token_comanda" core/ --include="*.py" | grep -v ".pyc"
echo ""

echo "2️⃣ BUSCAR ADMIN ACTIONS QUE GERAM LINKS:"
echo "───────────────────────────────────────────────────────────────"
grep -A 10 "def enviar_whatsapp" core/admin.py | head -15
echo ""

echo "3️⃣ BUSCAR COMO URL É CONSTRUÍDA:"
echo "───────────────────────────────────────────────────────────────"
grep -n "comanda.*http" core/ -r --include="*.py" | head -10
echo ""

echo "4️⃣ VERIFICAR views_whatsapp.py (se existir):"
echo "───────────────────────────────────────────────────────────────"
if [ -f "core/views_whatsapp.py" ]; then
    grep -A 5 "def gerar_mensagem" core/views_whatsapp.py | head -10
else
    echo "❌ Arquivo não existe"
fi
echo ""

echo "5️⃣ BUSCAR CONSTRUÇÃO DE URLs COM 'web':"
echo "───────────────────────────────────────────────────────────────"
grep -rn "/web/" core/ --include="*.py" | head -10
echo ""

echo "6️⃣ VERIFICAR TEMPLATES DE EMAIL:"
echo "───────────────────────────────────────────────────────────────"
find templates -name "*comanda*" -type f 2>/dev/null | head -5
echo ""

echo "════════════════════════════════════════════════════════════"
