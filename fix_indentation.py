#!/usr/bin/env python3
"""
Corrige indentação do admin.py
"""

with open('core/admin.py', 'r') as f:
    lines = f.readlines()

output = []
inside_comanda_admin = False
line_num = 0

for i, line in enumerate(lines, 1):
    # Detectar início da classe ComandaAdmin (linha 107)
    if 'class ComandaAdmin(admin.ModelAdmin):' in line and i == 107:
        inside_comanda_admin = True
        output.append(line)
        continue
    
    # Detectar fim da classe (próxima classe ou @admin.register)
    if inside_comanda_admin and i > 107:
        if (line.startswith('class ') and not line.startswith('    ')) or \
           (line.startswith('@admin.register') and not line.startswith('    ')):
            inside_comanda_admin = False
    
    # Se estamos dentro da ComandaAdmin e a linha começa com @admin.display ou def
    if inside_comanda_admin and (line.startswith('@admin.display') or line.startswith('def ')):
        # Adicionar 4 espaços se não tiver
        output.append('    ' + line)
    elif inside_comanda_admin and line.strip() and not line.startswith(' '):
        # Outras linhas sem indentação dentro da classe
        output.append('    ' + line)
    else:
        output.append(line)

# Backup
import shutil
shutil.copy('core/admin.py', 'core/admin.py.backup_indent')

# Salvar
with open('core/admin.py', 'w') as f:
    f.writelines(output)

print("✅ Indentação corrigida!")
print("📦 Backup em: core/admin.py.backup_indent")
