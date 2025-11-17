#!/bin/bash
# Testa se Celery está funcionando

echo "🧪 TESTANDO CELERY"
echo "=================="
echo ""

source venv/bin/activate

echo "1. Testando worker..."
celery -A sgli_project inspect ping

echo ""
echo "2. Testando task síncrona..."
python << 'PYEOF'
from core.tasks import enviar_notificacao_individual_task
print("✅ Import funcionou!")
PYEOF

echo ""
echo "3. Listando tasks registradas..."
celery -A sgli_project inspect registered

echo ""
echo "✅ TESTE CONCLUÍDO"
