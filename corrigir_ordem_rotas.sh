#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "🔧 CORREÇÃO CRÍTICA - ORDEM DAS ROTAS"
echo "════════════════════════════════════════════════════════════"
echo ""

# Backup
echo "📦 1/5 - Criando backup..."
cp core/urls.py core/urls.py.backup_rotas_$(date +%Y%m%d_%H%M%S)
echo "✅ Backup criado!"
echo ""

# Mostrar ordem atual
echo "🔍 2/5 - ORDEM ATUAL (ERRADA):"
echo "───────────────────────────────────────────────────────────────"
sed -n '28,29p' core/urls.py | cat -n
echo ""

# Aplicar correção
echo "🔧 3/5 - Invertendo ordem das rotas..."

python3 << 'PYTHON'
with open('core/urls.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar as duas linhas
linha_token = None
linha_email = None

for i, line in enumerate(lines):
    if 'comanda/<uuid:comanda_id>/<str:token>/' in line:
        linha_token = i
    if 'comanda/<uuid:comanda_id>/enviar-email/' in line:
        linha_email = i

if linha_token and linha_email:
    print(f"✅ Linha token encontrada: {linha_token + 1}")
    print(f"✅ Linha email encontrada: {linha_email + 1}")
    
    # Inverter as linhas
    lines[linha_token], lines[linha_email] = lines[linha_email], lines[linha_token]
    
    print(f"✅ Linhas invertidas!")
    
    with open('core/urls.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Arquivo salvo!")
else:
    print("❌ Erro: Não encontrei as linhas!")
    exit(1)
PYTHON

if [ $? -ne 0 ]; then
    echo "❌ ERRO! Revertendo..."
    cp core/urls.py.backup_rotas_* core/urls.py
    exit 1
fi

echo ""

# Mostrar ordem corrigida
echo "✅ 4/5 - ORDEM CORRIGIDA:"
echo "───────────────────────────────────────────────────────────────"
sed -n '28,29p' core/urls.py | cat -n
echo ""

# Validar sintaxe
echo "🧪 5/5 - Validando sintaxe Python..."
python3 -m py_compile core/urls.py
if [ $? -eq 0 ]; then
    echo "✅ Sintaxe válida!"
else
    echo "❌ ERRO de sintaxe! Revertendo..."
    cp core/urls.py.backup_rotas_* core/urls.py
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ CORREÇÃO APLICADA COM SUCESSO!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 RESULTADO:"
echo "  Linha 28: /comanda/{id}/enviar-email/ (específica) ✅"
echo "  Linha 29: /comanda/{id}/{token}/ (genérica) ✅"
echo ""
echo "🎯 POR QUE ISSO RESOLVE:"
echo "  • Django testa rotas na ordem que aparecem"
echo "  • Rotas específicas devem vir ANTES de genéricas"
echo "  • Agora 'enviar-email' é detectado corretamente"
echo "  • Tokens SHA256 continuam funcionando"
echo ""
echo "🧪 TESTE AGORA:"
echo "  1. Reinicie o servidor: python manage.py runserver"
echo "  2. Acesse admin e clique em 📧 Email"
echo "  3. Deve funcionar sem erro!"
echo ""
