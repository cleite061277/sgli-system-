#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "🔍 DIAGNÓSTICO ERROS VISTORIAS - $(date '+%d/%m/%Y %H:%M')"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "1️⃣ DEPENDÊNCIAS INSTALADAS (LOCAL):"
pip list | grep -E "(boto3|django-storages|Pillow)" || echo "   ❌ Nenhuma encontrada"
echo ""

echo "2️⃣ REQUIREMENTS.TXT:"
grep -E "(boto3|django-storages)" requirements.txt || echo "   ⚠️ boto3 FALTANDO!"
echo ""

echo "3️⃣ SETTINGS.PY - CONFIGURAÇÃO R2:"
grep -A 5 "AWS_ACCESS_KEY_ID" sgli_project/settings.py | head -10
echo ""

echo "4️⃣ VARIÁVEIS DE AMBIENTE (LOCAL):"
echo "   R2_ACCESS_KEY_ID: ${R2_ACCESS_KEY_ID:-❌ NÃO DEFINIDA}"
echo "   R2_SECRET_ACCESS_KEY: ${R2_SECRET_ACCESS_KEY:-❌ NÃO DEFINIDA}"
echo "   R2_BUCKET_NAME: ${R2_BUCKET_NAME:-❌ NÃO DEFINIDA}"
echo "   R2_ENDPOINT_URL: ${R2_ENDPOINT_URL:-❌ NÃO DEFINIDA}"
echo ""

echo "5️⃣ TESTAR IMPORTAÇÃO BOTO3:"
python << 'PYEOF'
try:
    import boto3
    print("   ✅ boto3 importado com sucesso")
    print(f"   Versão: {boto3.__version__}")
except ImportError as e:
    print(f"   ❌ ERRO: {e}")
PYEOF
echo ""

echo "6️⃣ TESTAR DJANGO-STORAGES:"
python << 'PYEOF'
try:
    import storages
    print("   ✅ django-storages importado")
except ImportError as e:
    print(f"   ❌ ERRO: {e}")
PYEOF
echo ""

echo "7️⃣ VERIFICAR VIEWS INSPECTION:"
grep -n "import boto3" core/views_inspection.py || echo "   ℹ️ Não usa boto3 diretamente (OK)"
echo ""

echo "8️⃣ LOGS DE ERRO (se existir):"
tail -20 logs/django.log 2>/dev/null || echo "   ℹ️ Sem arquivo de log local"
echo ""

echo "════════════════════════════════════════════════════════════"
echo "✅ DIAGNÓSTICO CONCLUÍDO"
echo "════════════════════════════════════════════════════════════"
