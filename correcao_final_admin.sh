#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "🔧 CORREÇÃO FINAL - ADMIN.PY (Botão Email)"
echo "════════════════════════════════════════════════════════════"
echo ""

# Backup
echo "📦 1/5 - Criando backup final..."
cp core/admin.py core/admin.py.backup_final_$(date +%Y%m%d_%H%M%S)
echo "✅ Backup criado!"
echo ""

# Mostrar estado atual
echo "🔍 2/5 - Estado ATUAL (ERRADO):"
echo "───────────────────────────────────────────────────────────────"
sed -n '1139,1142p' core/admin.py | cat -n
echo ""

# Aplicar correção
echo "🔧 3/5 - Aplicando correção final..."
python3 << 'PYTHON'
with open('core/admin.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    # Botão Email (linha ~1140)
    if '📧 Email' in line and 'href="{}"' in line:
        lines[i] = line.replace(
            'href="{}" target="_blank"',
            'href="/comanda/{}/enviar-email/"'
        )
        print(f"✅ Linha {i+1}: Botão Email revertido para action admin")
    
    # Parâmetros (linha ~1142)
    if 'wa_url, comanda_url, comanda_url' in line:
        lines[i] = line.replace(
            'wa_url, comanda_url, comanda_url',
            'wa_url, obj.id, comanda_url'
        )
        print(f"✅ Linha {i+1}: Parâmetros corrigidos")

with open('core/admin.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Correções aplicadas!")
PYTHON

echo ""

# Mostrar estado corrigido
echo "✅ 4/5 - Estado CORRIGIDO:"
echo "───────────────────────────────────────────────────────────────"
sed -n '1139,1142p' core/admin.py | cat -n
echo ""

# Validar sintaxe
echo "🧪 5/5 - Validando sintaxe Python..."
python3 -m py_compile core/admin.py
if [ $? -eq 0 ]; then
    echo "✅ Sintaxe válida!"
else
    echo "❌ ERRO! Revertendo..."
    cp core/admin.py.backup_final_* core/admin.py
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ CORREÇÃO FINAL CONCLUÍDA COM SUCESSO!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 RESULTADO FINAL DOS 3 BOTÕES:"
echo ""
echo "  💬 WhatsApp:"
echo "     • Abre: WhatsApp com mensagem"
echo "     • Mensagem contém: Link público da comanda"
echo "     • Parâmetro: wa_url"
echo ""
echo "  📧 Email:"
echo "     • Ação: ENVIA EMAIL para locatário"
echo "     • Email contém: Todos os dados + link público"
echo "     • Rota: /comanda/{id}/enviar-email/"
echo "     • View: enviar_comanda_email() em core/views.py"
echo "     • Parâmetro: obj.id"
echo ""
echo "  👁️ Ver:"
echo "     • Abre: Link público diretamente no navegador"
echo "     • URL: /comanda/{id}/{token}/"
echo "     • Sem pedir login"
echo "     • Parâmetro: comanda_url"
echo ""
echo "🎯 TESTE LOCAL (recomendado):"
echo "  1. python manage.py runserver"
echo "  2. Acesse: http://localhost:8000/admin/core/comanda/"
echo "  3. Teste os 3 botões em qualquer comanda"
echo ""
echo "📦 DEPLOY (após teste local):"
echo "  git add core/admin.py"
echo "  git commit -m 'fix: corrigir botão Ver para usar link público com token'"
echo "  git push origin main"
echo ""
