#!/bin/bash

# ═══════════════════════════════════════════════════════════
# ETAPA 2: BOTÃO RECIBO EM CADA PAGAMENTO
# ═══════════════════════════════════════════════════════════

echo "════════════════════════════════════════════════════════"
echo "🎯 ETAPA 2: Implementando Botão Recibo em Pagamentos"
echo "════════════════════════════════════════════════════════"
echo ""

# Fazer backup
echo "📦 Criando backup de admin.py..."
cp ~/sgli_system/core/admin.py ~/sgli_system/core/admin.py.backup_etapa2_$(date +%Y%m%d_%H%M%S)

echo "✏️  Adicionando coluna 'botao_recibo' ao PagamentoAdmin..."

# Criar script Python para adicionar o botão
cat > /tmp/add_botao_recibo.py << 'PYTHON_EOF'
#!/usr/bin/env python3
import sys

# Ler admin.py
with open('/home/claude/sgli_system/core/admin.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar PagamentoAdmin
pagamento_admin_line = None
for i, line in enumerate(lines):
    if 'class PagamentoAdmin(admin.ModelAdmin)' in line:
        pagamento_admin_line = i
        break

if pagamento_admin_line is None:
    print("❌ PagamentoAdmin não encontrado!")
    sys.exit(1)

# Verificar se botao_recibo já existe
already_exists = False
for i in range(pagamento_admin_line, min(pagamento_admin_line + 200, len(lines))):
    if 'def botao_recibo' in lines[i]:
        already_exists = True
        break

if already_exists:
    print("✅ Botão de recibo já existe! Nada a fazer.")
    sys.exit(0)

# Encontrar list_display em PagamentoAdmin
list_display_line = None
for i in range(pagamento_admin_line, min(pagamento_admin_line + 50, len(lines))):
    if 'list_display' in lines[i] and '=' in lines[i]:
        list_display_line = i
        break

if list_display_line is None:
    print("❌ list_display não encontrado em PagamentoAdmin!")
    sys.exit(1)

# Encontrar fechamento do list_display
list_display_end = list_display_line
for i in range(list_display_line, min(list_display_line + 10, len(lines))):
    if ')' in lines[i]:
        list_display_end = i
        break

# Adicionar 'botao_recibo' ao list_display (antes do fechamento)
lines[list_display_end] = lines[list_display_end].replace(')', ", 'botao_recibo')")

# Encontrar onde inserir o método (após locatario_nome)
insert_line = None
for i in range(list_display_end, min(pagamento_admin_line + 200, len(lines))):
    if 'def locatario_nome' in lines[i]:
        # Procurar fim deste método
        for j in range(i, min(i + 10, len(lines))):
            if lines[j].strip().startswith('locatario_nome.short_description'):
                insert_line = j + 1
                break
        break

if insert_line is None:
    # Inserir após save_model
    for i in range(list_display_end, len(lines)):
        if 'def save_model' in lines[i]:
            # Encontrar fim do método
            for j in range(i, min(i + 20, len(lines))):
                if lines[j].strip().startswith('def ') and j > i:
                    insert_line = j
                    break
            break

if insert_line is None:
    insert_line = list_display_end + 20

# Adicionar método botao_recibo
new_method = '''
    @admin.display(description='🧾 Recibo')
    def botao_recibo(self, obj):
        """Botão para visualizar/enviar recibo (apenas pagamentos confirmados)"""
        from django.utils.html import format_html
        from django.urls import reverse
        
        # Só mostrar botão para pagamentos CONFIRMADOS
        if obj.status == 'confirmado':
            url = reverse('pagina_recibo_pagamento', kwargs={'pagamento_id': obj.id})
            return format_html(
                '<a href="{}" target="_blank" style="'
                'display: inline-block; '
                'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
                'color: white; '
                'padding: 6px 14px; '
                'border-radius: 6px; '
                'text-decoration: none; '
                'font-weight: bold; '
                'font-size: 12px; '
                'transition: all 0.3s; '
                'box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);'
                '" onmouseover="this.style.transform=\'translateY(-2px)\'; '
                'this.style.boxShadow=\'0 4px 12px rgba(102, 126, 234, 0.5)\';" '
                'onmouseout="this.style.transform=\'translateY(0)\'; '
                'this.style.boxShadow=\'0 2px 8px rgba(102, 126, 234, 0.3)\';">'
                '🧾 Recibo</a>',
                url
            )
        else:
            return format_html(
                '<span style="color: #999; font-size: 11px;">⏳ Aguardando confirmação</span>'
            )
    
'''

lines.insert(insert_line, new_method)

# Salvar
with open('/home/claude/sgli_system/core/admin.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Botão de recibo adicionado com sucesso!")
print(f"   Inserido na linha {insert_line}")
PYTHON_EOF

chmod +x /tmp/add_botao_recibo.py
python3 /tmp/add_botao_recibo.py

if [ $? -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "✅ ETAPA 2 CONCLUÍDA COM SUCESSO!"
    echo "════════════════════════════════════════════════════════"
    echo ""
    echo "📋 Modificações aplicadas:"
    echo "   • Coluna 'botao_recibo' adicionada ao list_display"
    echo "   • Método botao_recibo() criado"
    echo "   • Botão só aparece para status='confirmado'"
    echo "   • Abre página de recibo em nova aba"
    echo "   • Página já tem WhatsApp + Email + Download"
    echo ""
else
    echo ""
    echo "❌ ERRO na aplicação. Restaurando backup..."
    cp ~/sgli_system/core/admin.py.backup_etapa2_* ~/sgli_system/core/admin.py
    exit 1
fi
