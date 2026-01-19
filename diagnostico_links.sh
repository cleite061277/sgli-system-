#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "🔍 DIAGNÓSTICO - LINKS PÚBLICOS COMANDAS"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "1️⃣ URL PATTERN (deve ter <str:token>):"
echo "───────────────────────────────────────────────────────────────"
grep -n "comanda.*comanda_id" core/urls.py | head -3
echo ""

echo "2️⃣ ASSINATURA DA VIEW (deve ter 'token' como parâmetro):"
echo "───────────────────────────────────────────────────────────────"
grep -A 1 "def comanda_web_view" core/views_comanda_web.py
echo ""

echo "3️⃣ VALIDAÇÃO DE TOKEN (linha ~93):"
echo "───────────────────────────────────────────────────────────────"
sed -n '90,95p' core/views_comanda_web.py
echo ""

echo "4️⃣ FUNÇÃO DE GERAÇÃO DE TOKEN:"
echo "───────────────────────────────────────────────────────────────"
grep -A 3 "def gerar_token_comanda" core/views_comanda_web.py
echo ""

echo "5️⃣ FUNÇÃO DE VALIDAÇÃO:"
echo "───────────────────────────────────────────────────────────────"
grep -A 2 "def validar_token_comanda" core/views_comanda_web.py
echo ""

echo "════════════════════════════════════════════════════════════"
