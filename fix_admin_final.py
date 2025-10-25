#!/usr/bin/env python3
import re

with open('core/admin.py', 'r') as f:
    content = f.read()

# Encontrar onde começa a classe ComandaAdmin (linha 107)
lines = content.split('\n')

# Encontrar início e fim da classe
start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if i == 106 and 'class ComandaAdmin(admin.ModelAdmin):' in line:  # linha 107 (índice 106)
        start_idx = i
    
    # Encontrar próxima classe ou @admin.register no nível raiz
    if start_idx is not None and i > start_idx:
        if (line.startswith('class ') or line.startswith('@admin.register')) and not line.startswith('    '):
            end_idx = i
            break

if start_idx is None:
    print("❌ Classe ComandaAdmin não encontrada na linha 107")
    exit(1)

if end_idx is None:
    # Se não encontrou o fim, vai até o final
    end_idx = len(lines)

print(f"📍 Classe encontrada: linhas {start_idx+1} a {end_idx}")

# Processar linhas dentro da classe
new_lines = lines[:start_idx+1]  # Até a linha da classe

for i in range(start_idx+1, end_idx):
    line = lines[i]
    
    # Se a linha já tem indentação, manter
    if line.startswith('    '):
        new_lines.append(line)
    # Se é linha vazia, manter
    elif not line.strip():
        new_lines.append(line)
    # Caso contrário, adicionar 4 espaços
    else:
        new_lines.append('    ' + line)

# Adicionar o resto do arquivo
new_lines.extend(lines[end_idx:])

# Backup
import shutil
shutil.copy('core/admin.py', 'core/admin.py.backup_final')

# Salvar
with open('core/admin.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("✅ Admin.py corrigido!")
print("📦 Backup: core/admin.py.backup_final")
