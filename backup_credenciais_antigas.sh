#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🔄 Criando backup das credenciais antigas..."

# Backup railway_env_variables.txt
if [ -f "railway_env_variables.txt" ]; then
    cp railway_env_variables.txt "railway_env_variables.txt.backup_$TIMESTAMP"
    echo "✅ Backup: railway_env_variables.txt.backup_$TIMESTAMP"
fi

# Backup RENOVACAO_R2_2027.md (se existir)
if [ -f "RENOVACAO_R2_2027.md" ]; then
    cp RENOVACAO_R2_2027.md "RENOVACAO_R2_2027.md.backup_$TIMESTAMP"
    echo "✅ Backup: RENOVACAO_R2_2027.md.backup_$TIMESTAMP"
fi

echo ""
echo "📋 CREDENCIAIS ANTIGAS (backup):"
grep "R2_ACCESS_KEY_ID\|R2_SECRET_ACCESS_KEY\|R2_ENDPOINT_URL" "railway_env_variables.txt.backup_$TIMESTAMP" | head -3

echo ""
echo "✅ Backups criados com sucesso!"
