#!/usr/bin/env bash
# reindent_admin.sh
# Script robust (copia-e-cola) para:
# - criar backups
# - normalizar tabs -> 4 espaços
# - reindentar automaticamente a classe ComandaAdmin em core/admin.py
# - gerar arquivo de preview em /tmp/core_admin_reindented.py
# - aplicar substituição somente se executado com --apply (sempre com rollback em caso de erro)
#
# Uso:
# 1) Verificar apenas preview:   bash reindent_admin.sh
# 2) Gerar e aplicar as mudanças: bash reindent_admin.sh --apply
#
# Execute na raiz do projeto (onde está o arquivo core/admin.py e manage.py).
# Recomendo ativar o virtualenv antes de aplicar (--apply) para que "manage.py check"
# rode no ambiente correto:
#   source venv/bin/activate
#
set -u

ADMIN_PY="core/admin.py"
PREVIEW="/tmp/core_admin_reindented.py"
TS=$(date +%Y%m%d_%H%M%S)
BACKUP_FULL="${ADMIN_PY}.bak.full_${TS}"
BACKUP_SCRIPT="${ADMIN_PY}.bak.script_${TS}"
APPLY=false

if [ "$#" -gt 0 ] && [ "$1" = "--apply" ]; then
  APPLY=true
fi

if [ ! -f "$ADMIN_PY" ]; then
  echo "ERRO: arquivo $ADMIN_PY não encontrado. Execute este script na raiz do projeto." >&2
  exit 1
fi

echo "1) Criando backup completo: $BACKUP_FULL"
cp -v "$ADMIN_PY" "$BACKUP_FULL" || { echo "Falha ao criar backup"; exit 1; }

echo "2) Normalizando tabs para 4 espaços (cria versão temporária)..."
TMP_EXPAND="/tmp/core_admin_expanded_${TS}.py"
expand -t 4 "$ADMIN_PY" > "$TMP_EXPAND" || { echo "Falha no expand"; exit 1; }

echo "3) Executando reindentação inteligente (preview em $PREVIEW)..."
python3 - <<'PY' > /tmp/reindent_admin_stdout.log 2>&1
import re, sys, shutil
p = "core/admin.py"
# use the expanded file we created
expanded = "'''TMP_EXPAND_PLACEHOLDER'''"
# replace placeholder with actual path
expanded = expanded.replace("'''TMP_EXPAND_PLACEHOLDER'''", "/tmp/core_admin_expanded_%s.py" % "$(date +%Y%m%d_%H%M%S)")
# But above substitution won't work inside heredoc; instead directly open /tmp/core_admin_expanded_* by glob:
import glob, codecs, os, fnmatch, io
exp_files = sorted(glob.glob("/tmp/core_admin_expanded_*.py"))
if not exp_files:
    print("ERRO: arquivo expand não encontrado em /tmp/core_admin_expanded_*.py", file=sys.stderr)
    sys.exit(2)
expanded_path = exp_files[-1]
s = open(expanded_path, "r", encoding="utf-8", errors="replace").read().splitlines()

# Ensure no tabs remain
s = [line.replace("\t", "    ") for line in s]

text = "\n".join(s) + ("\n" if len(s) and s[-1] == "" else "")

# find class ComandaAdmin or decorator + class
m = re.search(r'(^\s*@admin\.register\(\s*Comanda\s*\)\s*\n\s*class\s+ComandaAdmin\b.*:$)|(^\s*class\s+ComandaAdmin\b.*:$)', text, re.M)
if not m:
    print("ERRO: Não consegui localizar 'class ComandaAdmin' ou '@admin.register(Comanda) + class ComandaAdmin' em core/admin.py", file=sys.stderr)
    sys.exit(3)

# locate the line number of the class signature (0-based)
class_sig_idx = text[:m.start()].count("\n")
lines = text.splitlines()
n = len(lines)

# find end of class: first line after class_sig_idx that does NOT start with 4 spaces (or EOF)
j = class_sig_idx + 1
while j < n and (lines[j].startswith("    ") or lines[j].strip() == ""):
    j += 1
class_end_idx = j - 1

# Build new lines: keep everything up to and including class signature line
out = lines[:class_sig_idx+1]

i = class_sig_idx + 1

def is_top_member(idx):
    if idx >= n: return False
    return bool(re.match(r'^[ ]{4}(?:@|def\b|class\b)', lines[idx]))

def reindent_member(start_idx):
    j = start_idx
    block = []
    # collect decorators
    while j < n and re.match(r'^\s*@', lines[j]):
        block.append(lines[j])
        j += 1
    # expect def
    if j < n and re.match(r'^\s*def\b', lines[j]):
        block.append(lines[j])
        j += 1
    else:
        # nothing to do; return single line as-is
        return [lines[start_idx]], start_idx+1
    # collect body until next top-level member or end of class
    body = []
    while j < n and (lines[j].startswith("    ") or lines[j].strip() == "") and not re.match(r'^[ ]{4}(?:@|def\b|class\b)', lines[j]):
        body.append(lines[j])
        j += 1

    # normalize decorators/def to 4 spaces
    new_block = []
    for l in block:
        stripped = l.lstrip()
        new_block.append(" " * 4 + stripped)

    # reindent body with base 8 spaces
    base = 8
    indent = 0
    for raw in body:
        stripped = raw.lstrip()
        if stripped == "":
            new_block.append("")
            continue
        # dedent on elif/else/except/finally
        if re.match(r'^(elif\b|else:|except\b|finally:)', stripped):
            indent = max(indent - 1, 0)
        new_line = (" " * base) + (" " * (4 * indent)) + stripped
        new_block.append(new_line)
        # increase indent after lines that end with ':' and are not comments
        if stripped.endswith(":") and not stripped.strip().startswith("#"):
            indent += 1
    return new_block, j

while i <= class_end_idx and i < n:
    if is_top_member(i):
        new_block, next_i = reindent_member(i)
        out.extend(new_block)
        i = next_i
    else:
        # normalize other class-lines to at least 8 spaces if they start with spaces
        l = lines[i]
        if l.strip() == "":
            out.append("")
        else:
            if not l.startswith("    "):
                out.append(l)
            else:
                out.append(" " * 8 + l.lstrip())
        i += 1

# append remaining lines after class_end_idx
out.extend(lines[class_end_idx+1:])

new_text = "\n".join(out) + ("\n" if text.endswith("\n") else "")
# write preview
preview = "/tmp/core_admin_reindented.py"
with open(preview, "w", encoding="utf-8") as f:
    f.write(new_text)
print("Preview gravado em:", preview)
PY

# The heredoc above contained placeholders; to avoid complexity, run a simpler python script instead:
# We'll now run a cleaner Python reindent implementation that reads the expanded file we created.
python3 - <<'PY' > /tmp/reindent2_stdout.log 2>&1
import re, sys, glob
expanded_files = sorted(glob.glob('/tmp/core_admin_expanded_*.py'))
if not expanded_files:
    print('ERRO: arquivo expand não encontrado em /tmp/core_admin_expanded_*.py', file=sys.stderr)
    sys.exit(2)
expanded_path = expanded_files[-1]
with open(expanded_path, 'r', encoding='utf-8', errors='replace') as fh:
    lines = [ln.rstrip('\n') for ln in fh]

# Ensure tabs normalized
lines = [ln.replace('\t', '    ') for ln in lines]

text = '\n'.join(lines) + ('\n' if lines and lines[-1] == '' else '')

# Try to find class ComandaAdmin
m = re.search(r'(^\s*@admin\.register\(\s*Comanda\s*\)\s*\n\s*class\s+ComandaAdmin\b.*:$)|(^\s*class\s+ComandaAdmin\b.*:$)', text, re.M)
if not m:
    print('ERRO: Não localizei class ComandaAdmin', file=sys.stderr)
    sys.exit(3)

class_line = text[:m.start()].count('\n')
n = len(lines)

# find end of class: first line after class_line that does NOT start with 4 spaces (non-blank)
j = class_line + 1
while j < n and (lines[j].startswith('    ') or lines[j].strip() == ''):
    j += 1
class_end = j - 1

out = lines[:class_line+1]
i = class_line + 1

def is_top_member(idx):
    return idx < n and re.match(r'^[ ]{4}(?:@|def\b|class\b)', lines[idx])

def reindent_member_block(start):
    j = start
    block = []
    while j < n and re.match(r'^\s*@', lines[j]):
        block.append(lines[j])
        j += 1
    if j < n and re.match(r'^\s*def\b', lines[j]):
        block.append(lines[j])
        j += 1
    else:
        return [lines[start]], start+1
    body = []
    while j < n and (lines[j].startswith('    ') or lines[j].strip() == '') and not re.match(r'^[ ]{4}(?:@|def\b|class\b)', lines[j]):
        body.append(lines[j])
        j += 1
    new = []
    for l in block:
        new.append(' ' * 4 + l.lstrip())
    base = 8
    indent = 0
    for raw in body:
        stripped = raw.lstrip()
        if stripped == '':
            new.append('')
            continue
        if re.match(r'^(elif\b|else:|except\b|finally:)', stripped):
            indent = max(indent - 1, 0)
        new.append(' ' * base + ' ' * (4 * indent) + stripped)
        if stripped.endswith(':') and not stripped.strip().startswith('#'):
            indent += 1
    return new, j

while i <= class_end and i < n:
    if is_top_member(i):
        nb, ni = reindent_member_block(i)
        out.extend(nb)
        i = ni
    else:
        l = lines[i]
        if l.strip() == '':
            out.append('')
        else:
            if not l.startswith('    '):
                out.append(l)
            else:
                out.append(' ' * 8 + l.lstrip())
        i += 1

out.extend(lines[class_end+1:])
preview = "/tmp/core_admin_reindented.py"
with open(preview, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out) + ('\n' if text.endswith('\n') else ''))
print("Preview gerado em:", preview)
PY

if [ ! -f "$PREVIEW" ]; then
  echo "ERRO: preview não gerado; ver /tmp/reindent2_stdout.log e /tmp/reindent_admin_stdout.log" >&2
  echo "Saída do reindent2:" >&2
  sed -n '1,200p' /tmp/reindent2_stdout.log 2>/dev/null || true
  exit 1
fi

echo "4) Validando sintaxe do preview..."
python3 -m py_compile "$PREVIEW" 2>&1 | tee /tmp/py_compile_preview.log
if [ "${PIPESTATUS[0]}" -ne 0 ]; then
  echo "ERRO: preview tem problemas de sintaxe. Não aplicarei mudanças automaticamente."
  echo "Veja /tmp/py_compile_preview.log para detalhes."
  exit 1
fi

if [ "$APPLY" = false ]; then
  echo
  echo "PREVIEW OK. Revise o arquivo gerado em: $PREVIEW"
  echo "Se estiver satisfeito, execute o script com --apply para substituir core/admin.py."
  exit 0
fi

echo "5) Aplicando preview no arquivo real (backup adicional: $BACKUP_SCRIPT)..."
cp -v "$ADMIN_PY" "$BACKUP_SCRIPT" || { echo "Falha ao criar backup script"; exit 1; }
cp -v "$PREVIEW" "$ADMIN_PY" || { echo "Falha ao substituir $ADMIN_PY"; mv -v "$BACKUP_SCRIPT" "$ADMIN_PY"; exit 1; }

echo "6) Testando sintaxe e checagem do Django (py_compile + manage.py check)..."
python3 -m py_compile "$ADMIN_PY" 2>&1 | tee /tmp/py_compile_after_apply.log
if [ "${PIPESTATUS[0]}" -ne 0 ]; then
  echo "py_compile falhou após aplicar. Restaurando backup..."
  mv -v "$BACKUP_SCRIPT" "$ADMIN_PY"
  echo "Veja /tmp/py_compile_after_apply.log"
  exit 1
fi

if [ -f "manage.py" ]; then
  python3 manage.py check --traceback 2>&1 | tee /tmp/manage_check_after_apply.log
  if [ "${PIPESTATUS[0]}" -ne 0 ]; then
    echo "manage.py check falhou após aplicar. Restaurando backup..."
    mv -v "$BACKUP_SCRIPT" "$ADMIN_PY"
    echo "Veja /tmp/manage_check_after_apply.log"
    exit 1
  fi
else
  echo "Aviso: manage.py não encontrado; pulei a etapa 'manage.py check'."
fi

echo "OK: alterações aplicadas e validadas. Backups:"
ls -1 "${ADMIN_PY}.bak"* | sed -n '1,200p' || true
echo "Fim."