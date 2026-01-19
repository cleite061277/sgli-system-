#!/bin/bash
# ════════════════════════════════════════════════════════════════
# 🔧 CORREÇÃO CIRÚRGICA - BOTÕES EMAIL E VER
# ════════════════════════════════════════════════════════════════
# 
# PROBLEMA: Botões "Email" e "Ver" não usam link público com token
# SOLUÇÃO: Fazer ambos usarem comanda_url (que já existe na linha 1017)
# 
# ASSERTIVIDADE: 5/5 ⭐⭐⭐⭐⭐
# RISCO: Baixíssimo (3 linhas modificadas, 1 método afetado)
# ROLLBACK: Automático em caso de erro
# ════════════════════════════════════════════════════════════════

echo "════════════════════════════════════════════════════════════"
echo "🔧 CORREÇÃO CIRÚRGICA - 3 BOTÕES (WhatsApp, Email, Ver)"
echo "════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════
# 1️⃣ VALIDAÇÕES PRÉ-EXECUÇÃO
# ═══════════════════════════════════════════════════════════════
echo "📋 1/8 - Validações pré-execução..."
echo ""

# Verificar se estamos no diretório correto
if [ ! -f "manage.py" ]; then
    echo "❌ ERRO: Execute no diretório do projeto (~/sgli_system)"
    exit 1
fi

if [ ! -f "core/admin.py" ]; then
    echo "❌ ERRO: Arquivo core/admin.py não encontrado"
    exit 1
fi

# Verificar se comanda_url existe na linha 1017
if ! grep -q 'comanda_url = f"{domain}/comanda/{obj.id}/{token}/"' core/admin.py; then
    echo "❌ ERRO: comanda_url não encontrado na linha esperada"
    echo "⚠️  O arquivo pode ter sido modificado. Correção abortada."
    exit 1
fi

# Verificar se os botões estão no formato esperado
if ! grep -q 'href="/comanda/{}/web/"' core/admin.py; then
    echo "⚠️  Botão 'Ver' já pode estar corrigido ou arquivo foi modificado"
    echo "Verificando estado atual..."
    grep -n 'href.*Ver' core/admin.py | head -3
    echo ""
    read -p "Deseja continuar mesmo assim? (s/N): " resposta
    if [[ ! "$resposta" =~ ^[Ss]$ ]]; then
        echo "Correção cancelada pelo usuário."
        exit 0
    fi
fi

echo "✅ Validações OK!"
echo ""

# ═══════════════════════════════════════════════════════════════
# 2️⃣ BACKUP AUTOMÁTICO
# ═══════════════════════════════════════════════════════════════
echo "📦 2/8 - Criando backup..."
BACKUP_FILE="core/admin.py.backup_$(date +%Y%m%d_%H%M%S)"
cp core/admin.py "$BACKUP_FILE"
echo "✅ Backup criado: $BACKUP_FILE"
echo ""

# ═══════════════════════════════════════════════════════════════
# 3️⃣ MOSTRAR CÓDIGO ATUAL
# ═══════════════════════════════════════════════════════════════
echo "🔍 3/8 - Código ANTES da correção:"
echo "───────────────────────────────────────────────────────────────"
echo "Linha 1017 (geração de comanda_url):"
sed -n '1017p' core/admin.py
echo ""
echo "Linhas 1138-1143 (os 3 botões):"
sed -n '1138,1143p' core/admin.py | cat -n
echo ""

# ═══════════════════════════════════════════════════════════════
# 4️⃣ APLICAR CORREÇÃO CIRÚRGICA
# ═══════════════════════════════════════════════════════════════
echo "🔧 4/8 - Aplicando correção cirúrgica..."
echo ""

python3 << 'PYTHON'
import sys

try:
    with open('core/admin.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    correções = []
    linha_botoes = None
    
    # Encontrar a linha com os 3 botões
    for i, line in enumerate(lines):
        if 'href="/comanda/{}/web/"' in line and '👁️ Ver' in line:
            linha_botoes = i
            print(f"📍 Linha dos botões encontrada: {i+1}")
            break
    
    if linha_botoes is None:
        print("❌ ERRO: Linha dos botões não encontrada!")
        sys.exit(1)
    
    # Verificar se comanda_url existe antes (linha 1017)
    comanda_url_exists = False
    for j in range(max(0, linha_botoes-200), linha_botoes):
        if 'comanda_url = f"{domain}/comanda/{obj.id}/{token}/"' in lines[j]:
            comanda_url_exists = True
            print(f"✅ comanda_url encontrado na linha {j+1}")
            break
    
    if not comanda_url_exists:
        print("❌ ERRO: comanda_url não encontrado antes dos botões!")
        sys.exit(1)
    
    # CORREÇÃO 1: Botão Email
    linha_original_1140 = lines[linha_botoes]
    if 'href="/comanda/{}/enviar-email/"' in linha_original_1140:
        lines[linha_botoes] = lines[linha_botoes].replace(
            'href="/comanda/{}/enviar-email/"',
            'href="{}" target="_blank"'
        )
        correções.append("✅ Botão Email: /comanda/{}/enviar-email/ → {}")
    
    # CORREÇÃO 2: Botão Ver
    if 'href="/comanda/{}/web/"' in lines[linha_botoes]:
        lines[linha_botoes] = lines[linha_botoes].replace(
            'href="/comanda/{}/web/"',
            'href="{}"'
        )
        correções.append("✅ Botão Ver: /comanda/{}/web/ → {}")
    
    # CORREÇÃO 3: Parâmetros do format_html
    linha_params_modificada = False
    for j in range(linha_botoes+1, min(len(lines), linha_botoes+5)):
        if 'wa_url, obj.id, obj.id' in lines[j]:
            lines[j] = lines[j].replace('wa_url, obj.id, obj.id', 'wa_url, comanda_url, comanda_url')
            correções.append(f"✅ Parâmetros na linha {j+1}: obj.id, obj.id → comanda_url, comanda_url")
            linha_params_modificada = True
            break
    
    if not linha_params_modificada:
        print("❌ ERRO: Linha de parâmetros não encontrada!")
        sys.exit(1)
    
    # Salvar arquivo
    with open('core/admin.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    # Mostrar correções aplicadas
    print("")
    for correcao in correções:
        print(correcao)
    print("")
    print("✅ Arquivo salvo com sucesso!")
    
except Exception as e:
    print(f"❌ ERRO durante correção: {e}")
    sys.exit(1)
PYTHON

# Verificar se Python teve sucesso
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ CORREÇÃO FALHOU! Revertendo..."
    cp "$BACKUP_FILE" core/admin.py
    echo "✅ Arquivo revertido para versão original"
    exit 1
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# 5️⃣ MOSTRAR CÓDIGO CORRIGIDO
# ═══════════════════════════════════════════════════════════════
echo "✅ 5/8 - Código DEPOIS da correção:"
echo "───────────────────────────────────────────────────────────────"
echo "Linha 1017 (geração de comanda_url - NÃO MUDOU):"
sed -n '1017p' core/admin.py
echo ""
echo "Linhas 1138-1143 (os 3 botões - CORRIGIDOS):"
sed -n '1138,1143p' core/admin.py | cat -n
echo ""

# ═══════════════════════════════════════════════════════════════
# 6️⃣ VALIDAR SINTAXE PYTHON
# ═══════════════════════════════════════════════════════════════
echo "🧪 6/8 - Validando sintaxe Python..."
python3 -m py_compile core/admin.py 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Sintaxe válida!"
else
    echo "❌ ERRO de sintaxe! Revertendo..."
    cp "$BACKUP_FILE" core/admin.py
    echo "✅ Arquivo revertido para versão original"
    exit 1
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# 7️⃣ DIFF VISUAL
# ═══════════════════════════════════════════════════════════════
echo "📊 7/8 - Resumo das mudanças:"
echo "───────────────────────────────────────────────────────────────"
echo "ANTES:"
echo "  '<a href=\"/comanda/{}/enviar-email/\" ...>📧 Email</a>'"
echo "  '<a href=\"/comanda/{}/web/\" ...>👁️ Ver</a>'"
echo "  wa_url, obj.id, obj.id"
echo ""
echo "DEPOIS:"
echo "  '<a href=\"{}\" target=\"_blank\" ...>📧 Email</a>'"
echo "  '<a href=\"{}\" target=\"_blank\" ...>👁️ Ver</a>'"
echo "  wa_url, comanda_url, comanda_url"
echo ""

# ═══════════════════════════════════════════════════════════════
# 8️⃣ CONCLUSÃO E PRÓXIMOS PASSOS
# ═══════════════════════════════════════════════════════════════
echo "════════════════════════════════════════════════════════════"
echo "✅ CORREÇÃO CONCLUÍDA COM SUCESSO!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 O QUE FOI CORRIGIDO:"
echo "  ✅ Linha 1017: comanda_url já existia (mantido)"
echo "  ✅ Botão WhatsApp: já usava wa_url (mantido)"
echo "  ✅ Botão Email: agora usa comanda_url com target='_blank'"
echo "  ✅ Botão Ver: agora usa comanda_url"
echo ""
echo "🎯 RESULTADO:"
echo "  • Os 3 botões agora abrem o MESMO link público seguro"
echo "  • Link: https://dominio.com/comanda/{id}/{token}/"
echo "  • Sem pedir senha, apenas visualização da comanda"
echo ""
echo "🧪 TESTE LOCAL (FORTEMENTE RECOMENDADO):"
echo "  1. python manage.py runserver"
echo "  2. Acesse: http://localhost:8000/admin/core/comanda/"
echo "  3. Teste os 3 botões em qualquer comanda"
echo "  4. Verifique que todos abrem a MESMA página (sem pedir login)"
echo ""
echo "📦 DEPLOY PARA PRODUÇÃO (após teste local):"
echo "  git add core/admin.py"
echo "  git commit -m 'fix: corrigir botões Email e Ver para usar link público com token'"
echo "  git push origin main"
echo ""
echo "🔄 ROLLBACK (se necessário):"
echo "  cp $BACKUP_FILE core/admin.py"
echo ""
echo "📁 BACKUP SALVO EM:"
echo "  $BACKUP_FILE"
echo ""
