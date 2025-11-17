#!/bin/bash
# Script para iniciar workers do Celery

echo "🚀 INICIANDO CELERY WORKER E BEAT"
echo "=================================="
echo ""

# Ativar venv
source venv/bin/activate

# Matar processos anteriores
pkill -f "celery worker"
pkill -f "celery beat"

# Iniciar worker em background
celery -A sgli_project worker --loglevel=info --concurrency=2 &
WORKER_PID=$!
echo "✅ Worker iniciado (PID: $WORKER_PID)"

# Aguardar 3 segundos
sleep 3

# Iniciar beat em background
celery -A sgli_project beat --loglevel=info &
BEAT_PID=$!
echo "✅ Beat iniciado (PID: $BEAT_PID)"

echo ""
echo "=================================="
echo "✅ Celery rodando!"
echo "   Worker PID: $WORKER_PID"
echo "   Beat PID: $BEAT_PID"
echo ""
echo "📋 Para parar: pkill -f celery"
echo "=================================="
