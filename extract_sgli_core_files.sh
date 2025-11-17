#!/usr/bin/env bash
# Extrai os ficheiros relevantes do tar grande, cria small tar e um bundle txt com os ficheiros.
# Uso: ./extract_sgli_core_files.sh [path/to/sgli_debug_core_pagamento_*.tar.gz]
set -euo pipefail

BIGTAR="${1:-/tmp/sgli_debug_core_pagamento_20251105_235636.tar.gz}"
if [ ! -f "$BIGTAR" ]; then
  echo "ERRO: tar não encontrado em: $BIGTAR"
  echo "Procure por: ls -1t /tmp/sgli_debug_core_pagamento_*.tar.gz"
  exit 1
fi

TS=$(date +%Y%m%d_%H%M%S)
OUTDIR="/tmp/sgli_extract_${TS}"
LIST="/tmp/sgli_tarlist_${TS}.txt"
PATHS="/tmp/sgli_paths_to_extract_${TS}.txt"
SMALLTAR="/tmp/sgli_core_pagamento_small_${TS}.tar.gz"
BUNDLE="/tmp/sgli_core_pagamento_bundle_${TS}.txt"
LOG="/tmp/sgli_extract_run_${TS}.log"

mkdir -p "$OUTDIR"
echo "OUTDIR=$OUTDIR"
echo "LOG=$LOG"

{
  echo "=== Listando conteúdo do tar: $BIGTAR ==="
  tar -tzf "$BIGTAR" > "$LIST"
  echo "Lista escrita em: $LIST"
  echo
  echo "=== Procurando paths relevantes ==="
  # Paths exatos que queremos (core files + templates admin)
  grep -E '(^|/)(core/admin.py|core/dashboard_views.py|core/templates/admin/index.html|core/templates/admin/pagamento_recibo.html)$' "$LIST" | sort -u > "$PATHS" || true
  # também pegar possíveis index/pagamento_recibo em backups e templates
  tar -tzf "$BIGTAR" | grep -E 'index.html$|pagamento_recibo.html$' | grep -E 'admin|templates' | sort -u >> "$PATHS" || true
  sort -u "$PATHS" -o "$PATHS" || true

  echo "Paths a extrair (arquivo: $PATHS):"
  sed -n '1,200p' "$PATHS" || true
  echo

  echo "=== Tentando extrair usando -T (lista exata) ==="
  if [ -s "$PATHS" ]; then
    # tar -T pode falhar em alguns ambientes; tentamos e caímos no fallback
    if tar -xzf "$BIGTAR" -C "$OUTDIR" -T "$PATHS" 2>/tmp/extract_exact.err; then
      echo "Extração via -T OK"
    else
      echo "Extração via -T falhou (ver /tmp/extract_exact.err). Tentando fallback por padrão/wildcard."
      while IFS= read -r p || [ -n "$p" ]; do
        p="${p#./}"
        echo "-> extraindo (literal): $p"
        if tar -xzf "$BIGTAR" -C "$OUTDIR" "$p" 2>/dev/null; then
          echo "   OK literal"
          continue
        fi
        # fallback: wildcard (no-anchored)
        for pat in "./$p" "*$p" "*/$p" "$(basename "$p")"; do
          echo "   try pattern: $pat"
          if tar -xzf "$BIGTAR" -C "$OUTDIR" --wildcards --no-anchored "$pat" 2>/dev/null; then
            echo "     OK via pattern $pat"
            break
          fi
        done
      done < "$PATHS"
    fi
  else
    echo "Nenhum path identificado para extrair."
  fi

  echo
  echo "=== Conteúdo extraído em $OUTDIR (primeiras linhas) ==="
  ls -lR "$OUTDIR" | sed -n '1,300p' || true

  echo
  echo "=== Criando small tar: $SMALLTAR ==="
  tar -czf "$SMALLTAR" -C "$OUTDIR" . || { echo "Erro ao criar $SMALLTAR"; exit 1; }
  ls -lh "$SMALLTAR" || true

  echo
  echo "=== Criando bundle txt com os ficheiros relevantes: $BUNDLE ==="
  echo "=== core/admin.py ===" > "$BUNDLE" || true
  if [ -f "$OUTDIR/core/admin.py" ]; then
    sed -n '1,400p' "$OUTDIR/core/admin.py" >> "$BUNDLE"
  else
    echo "(não extraído: core/admin.py)" >> "$BUNDLE"
  fi
  echo -e "\n=== core/dashboard_views.py ===" >> "$BUNDLE"
  if [ -f "$OUTDIR/core/dashboard_views.py" ]; then
    sed -n '1,400p' "$OUTDIR/core/dashboard_views.py" >> "$BUNDLE"
  else
    echo "(não extraído: core/dashboard_views.py)" >> "$BUNDLE"
  fi
  echo -e "\n=== core/templates/admin/index.html ===" >> "$BUNDLE"
  if [ -f "$OUTDIR/core/templates/admin/index.html" ]; then
    sed -n '1,400p' "$OUTDIR/core/templates/admin/index.html" >> "$BUNDLE"
  else
    echo "(não extraído: core/templates/admin/index.html)" >> "$BUNDLE"
  fi
  echo -e "\n=== core/templates/admin/pagamento_recibo.html ===" >> "$BUNDLE"
  if [ -f "$OUTDIR/core/templates/admin/pagamento_recibo.html" ]; then
    sed -n '1,400p' "$OUTDIR/core/templates/admin/pagamento_recibo.html" >> "$BUNDLE"
  else
    echo "(não extraído: core/templates/admin/pagamento_recibo.html)" >> "$BUNDLE"
  fi

  echo "Bundle criado: $BUNDLE"
  echo "Lista de arquivos dentro do small tar (até 200 linhas):"
  tar -tzf "$SMALLTAR" | sed -n '1,200p' || true

  # tentar gerar admin_registry and url_names files via manage.py, se existir
  if [ -f manage.py ]; then
    echo "Tentando gerar admin_registry e url names via manage.py (arquivo de saída em /tmp)..."
    python3 manage.py shell -c "from django.contrib import admin; \
print('\\n'.join(f'{m._meta.app_label}.{m._meta.model_name}' for m in admin.site._registry))" \
      > "/tmp/admin_registry_${TS}.txt" 2>/tmp/admin_registry_err_${TS}.log || echo "Não foi possível gerar admin_registry (ver /tmp/admin_registry_err_${TS}.log)"
    python3 manage.py shell -c "from django.urls import get_resolver; \
print('\\n'.join([n for n in get_resolver(None).reverse_dict.keys() if isinstance(n,str) and 'pagamento' in n]) or '<no-names-found>')" \
      > "/tmp/url_names_with_pagamento_${TS}.txt" 2>/tmp/url_names_err_${TS}.log || echo "Não foi possível gerar url_names (ver /tmp/url_names_err_${TS}.log)"
    echo "Possíveis outputs: /tmp/admin_registry_${TS}.txt , /tmp/url_names_with_pagamento_${TS}.txt"
  else
    echo "manage.py não encontrado aqui — pulei inspeção Django."
  fi

  echo
  echo "Arquivos gerados:"
  ls -lh "$LIST" "$PATHS" "$SMALLTAR" "$BUNDLE" /tmp/admin_registry_${TS}.txt /tmp/url_names_with_pagamento_${TS}.txt 2>/dev/null || true
} 2>&1 | tee "$LOG"

echo
echo "Concluído. Log salvo em: $LOG"
echo "Se quiser enviar o small tar para download (p.ex. baixar para o seu PC), use scp ou inicie um servidor http: cd /tmp && python3 -m http.server 8000 --bind 0.0.0.0"