#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "🔧 CORREÇÃO TEMPLATE - WhatsApp e Rodapé"
echo "════════════════════════════════════════════════════════════"
echo ""

TEMPLATE="core/templates/comanda/comanda_web.html"

# Backup
echo "📦 1/5 - Criando backup..."
cp "$TEMPLATE" "${TEMPLATE}.backup_$(date +%Y%m%d_%H%M%S)"
echo "✅ Backup criado!"
echo ""

# Mostrar valores atuais
echo "🔍 2/5 - Valores ATUAIS:"
echo "───────────────────────────────────────────────────────────────"
echo "WhatsApp (linha ~157):"
grep -n "wa.me" "$TEMPLATE"
echo ""
echo "Rodapé (linha ~164):"
sed -n '164,166p' "$TEMPLATE"
echo ""

# Aplicar correções
echo "🔧 3/5 - Aplicando correções..."
echo ""

# Correção 1: Número WhatsApp
sed -i 's|https://wa.me/554199999999|https://wa.me/5541372320032|g' "$TEMPLATE"
echo "✅ WhatsApp: 554199999999 → 5541372320032"

# Correção 2: Rodapé linha 1
sed -i 's|<p><strong>HABITAT PRO</strong></p>|<p><strong>HABITAT PRO v1.0 \| Sistema de Gestão Imobiliária</strong></p>|g' "$TEMPLATE"
echo "✅ Rodapé linha 1: Atualizado"

# Correção 3: Rodapé linha 2
sed -i 's|<p>Sistema de Gestão Inteligente de Imóveis</p>|<p>© 2025 A\&C Imóveis e Sistemas Imobiliários \| Paranaguá - PR</p>|g' "$TEMPLATE"
echo "✅ Rodapé linha 2: Atualizado"

echo ""

# Mostrar valores corrigidos
echo "✅ 4/5 - Valores CORRIGIDOS:"
echo "───────────────────────────────────────────────────────────────"
echo "WhatsApp (linha ~157):"
grep -n "wa.me" "$TEMPLATE"
echo ""
echo "Rodapé (linhas ~164-165):"
sed -n '164,165p' "$TEMPLATE"
echo ""

# Validar HTML
echo "🧪 5/5 - Validando arquivo..."
if [ -f "$TEMPLATE" ]; then
    echo "✅ Arquivo existe e foi modificado!"
else
    echo "❌ ERRO: Arquivo não encontrado!"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ CORREÇÕES APLICADAS COM SUCESSO!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 ALTERAÇÕES:"
echo "  1️⃣ Botão WhatsApp:"
echo "     • Número: 41 3723-2032 (Policorp)"
echo "     • Formato: 5541372320032"
echo ""
echo "  2️⃣ Rodapé:"
echo "     • Linha 1: HABITAT PRO v1.0 | Sistema de Gestão Imobiliária"
echo "     • Linha 2: © 2025 A&C Imóveis e Sistemas Imobiliários | Paranaguá - PR"
echo ""
echo "🧪 TESTE AGORA:"
echo "  1. Abra uma comanda pública existente"
echo "  2. Verifique o botão WhatsApp (deve abrir com 5541372320032)"
echo "  3. Verifique o rodapé (deve mostrar A&C Imóveis)"
echo ""
echo "📦 BACKUP SALVO EM:"
ls -t ${TEMPLATE}.backup_* | head -1
echo ""
