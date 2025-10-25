#!/bin/bash
# Script para iniciar Django-Q worker
# Uso: ./iniciar_worker.sh

cd ~/sgli_system
source venv/bin/activate

echo "════════════════════════════════════════════"
echo "🚀 INICIANDO DJANGO-Q WORKER"
echo "════════════════════════════════════════════"
echo ""
echo "⚠️  O worker ficará rodando em primeiro plano"
echo "   Para parar: Ctrl+C"
echo ""
echo "💡 Para rodar em background:"
echo "   nohup ./iniciar_worker.sh > worker.log 2>&1 &"
echo ""
echo "════════════════════════════════════════════"
echo ""

python manage.py qcluster
