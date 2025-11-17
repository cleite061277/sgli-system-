#!/bin/bash

# ═══════════════════════════════════════════════════════════
# ETAPA 1: ALERTA CONTRATOS VENCENDO EM 60 DIAS
# ═══════════════════════════════════════════════════════════

echo "════════════════════════════════════════════════════════"
echo "🎯 ETAPA 1: Implementando Alerta 60 Dias"
echo "════════════════════════════════════════════════════════"
echo ""

# Fazer backup
echo "📦 Criando backup de admin.py..."
cp ~/sgli_system/core/admin.py ~/sgli_system/core/admin.py.backup_$(date +%Y%m%d_%H%M%S)

# Encontrar linha do LocacaoAdmin
echo "🔍 Localizando LocacaoAdmin..."
grep -n "class LocacaoAdmin" ~/sgli_system/core/admin.py | head -1

echo ""
echo "✏️  Adicionando método alerta_vencimento ao LocacaoAdmin..."

# Criar arquivo Python temporário com a modificação
cat > /tmp/add_alerta_vencimento.py << 'PYTHON_EOF'
#!/usr/bin/env python3
import sys

# Ler o arquivo admin.py
with open('/home/claude/sgli_system/core/admin.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar a classe LocacaoAdmin
locacao_admin_line = None
for i, line in enumerate(lines):
    if 'class LocacaoAdmin(admin.ModelAdmin)' in line:
        locacao_admin_line = i
        break

if locacao_admin_line is None:
    print("❌ LocacaoAdmin não encontrado!")
    sys.exit(1)

# Encontrar list_display dentro de LocacaoAdmin
list_display_line = None
for i in range(locacao_admin_line, min(locacao_admin_line + 50, len(lines))):
    if 'list_display' in lines[i] and '=' in lines[i]:
        list_display_line = i
        break

if list_display_line is None:
    print("❌ list_display não encontrado em LocacaoAdmin!")
    sys.exit(1)

# Verificar se alerta_vencimento já existe
already_exists = False
for i in range(locacao_admin_line, min(locacao_admin_line + 200, len(lines))):
    if 'def alerta_vencimento' in lines[i]:
        already_exists = True
        break

if already_exists:
    print("✅ Alerta de vencimento já existe! Nada a fazer.")
    sys.exit(0)

# Adicionar 'alerta_vencimento' ao list_display
# Procurar o fechamento do list_display
list_display_end = list_display_line
bracket_count = 0
started = False
for i in range(list_display_line, min(list_display_line + 30, len(lines))):
    line = lines[i]
    if '[' in line:
        started = True
        bracket_count += line.count('[')
    if started:
        bracket_count -= line.count(']')
        if bracket_count == 0:
            list_display_end = i
            break

# Inserir 'alerta_vencimento' antes do fechamento
if ']' in lines[list_display_end]:
    # Verificar se já existe
    full_list_display = ''.join(lines[list_display_line:list_display_end+1])
    if 'alerta_vencimento' not in full_list_display:
        # Adicionar antes do ]
        lines[list_display_end] = lines[list_display_end].replace(']', "        'alerta_vencimento',\n    ]")

# Encontrar onde adicionar o método (procurar próximo método def após list_display)
insert_line = None
for i in range(list_display_end + 1, min(list_display_end + 100, len(lines))):
    if lines[i].strip().startswith('def ') or lines[i].strip().startswith('class '):
        insert_line = i
        break

if insert_line is None:
    # Se não encontrar, adicionar antes do final da classe
    for i in range(len(lines) - 1, locacao_admin_line, -1):
        if 'class ' in lines[i] and i > locacao_admin_line:
            insert_line = i
            break

if insert_line is None:
    insert_line = list_display_end + 5

# Adicionar método alerta_vencimento
new_method = '''
    @admin.display(description='⚠️ Alerta Vencimento', ordering='data_fim')
    def alerta_vencimento(self, obj):
        """Exibe alerta para contratos vencendo em até 60 dias"""
        from django.utils import timezone
        from django.utils.html import format_html
        
        if not obj.data_fim:
            return '-'
        
        hoje = timezone.now().date()
        dias_restantes = (obj.data_fim - hoje).days
        
        # Contratos vencendo em 60 dias ou menos
        if 0 <= dias_restantes <= 60:
            if dias_restantes <= 7:
                cor = '#dc3545'  # Vermelho urgente
                icon = '🚨'
            elif dias_restantes <= 30:
                cor = '#fd7e14'  # Laranja
                icon = '⚠️'
            else:
                cor = '#ffc107'  # Amarelo
                icon = '⏰'
            
            return format_html(
                '<span style="color: {}; font-weight: bold; background: {}; '
                'padding: 4px 10px; border-radius: 12px; font-size: 12px;">'
                '{} {} dia(s)</span>',
                cor,
                f'{cor}20',  # Cor de fundo com transparência
                icon,
                dias_restantes
            )
        elif dias_restantes < 0:
            dias_vencido = abs(dias_restantes)
            return format_html(
                '<span style="color: #dc3545; font-weight: bold; background: #dc354520; '
                'padding: 4px 10px; border-radius: 12px; font-size: 12px;">'
                '❌ Vencido há {} dia(s)</span>',
                dias_vencido
            )
        else:
            return format_html(
                '<span style="color: #28a745;">✅ OK</span>'
            )
    
'''

lines.insert(insert_line, new_method)

# Salvar arquivo
with open('/home/claude/sgli_system/core/admin.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Método alerta_vencimento adicionado com sucesso!")
print(f"   Inserido na linha {insert_line}")
PYTHON_EOF

chmod +x /tmp/add_alerta_vencimento.py
python3 /tmp/add_alerta_vencimento.py

if [ $? -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "✅ ETAPA 1 CONCLUÍDA COM SUCESSO!"
    echo "════════════════════════════════════════════════════════"
    echo ""
    echo "📋 Modificações aplicadas:"
    echo "   • list_display atualizado com 'alerta_vencimento'"
    echo "   • Método alerta_vencimento() criado"
    echo "   • Alertas visuais:"
    echo "     🚨 Vermelho: ≤7 dias"
    echo "     ⚠️  Laranja: ≤30 dias"
    echo "     ⏰ Amarelo: ≤60 dias"
    echo "     ❌ Vencidos"
    echo ""
else
    echo ""
    echo "❌ ERRO na aplicação. Restaurando backup..."
    cp ~/sgli_system/core/admin.py.backup_* ~/sgli_system/core/admin.py
    exit 1
fi
