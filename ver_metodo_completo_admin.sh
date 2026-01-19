#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "🔍 MÉTODO COMPLETO QUE GERA OS 3 BOTÕES"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "1️⃣ MÉTODO COMPLETO (30 linhas antes até 10 depois da linha 1141):"
echo "───────────────────────────────────────────────────────────────"
sed -n '1110,1150p' core/admin.py | cat -n
echo ""

echo "2️⃣ VERIFICAR SE gerar_token_comanda JÁ É IMPORTADO:"
echo "───────────────────────────────────────────────────────────────"
head -30 core/admin.py | grep -E "gerar_token_comanda"
echo ""

echo "3️⃣ VERIFICAR SE TOKEN JÁ É GERADO NO MÉTODO:"
echo "───────────────────────────────────────────────────────────────"
sed -n '1110,1150p' core/admin.py | grep -i "token"
echo ""

echo "════════════════════════════════════════════════════════════"
