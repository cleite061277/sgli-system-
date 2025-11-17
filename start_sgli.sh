#!/bin/bash
# Carregar variáveis de ambiente do .env
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Script de inicialização do SGLI

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

cd ~/sgli_system
source venv/bin/activate

echo -e "${GREEN}🚀 INICIANDO SGLI - Sistema de Gestão de Locação de Imóveis${NC}"
echo -e "${BLUE}================================================${NC}"
echo
echo "📍 Diretório: $(pwd)"
echo "🌐 URL Local: http://localhost:8000"
echo "🔐 Admin: http://localhost:8000/admin"
echo "👤 Usuário: admin"
echo "🔑 Senha: sgli@2024"
echo
echo "⏹️  Para parar o servidor: Ctrl+C"
echo -e "${BLUE}================================================${NC}"
echo

# Verificar se todos os serviços estão rodando
echo "🔍 Verificando serviços..."
sudo systemctl is-active --quiet postgresql || sudo systemctl start postgresql
sudo systemctl is-active --quiet redis-server || sudo systemctl start redis-server

echo "✅ Serviços verificados!"
echo

# Executar migrações se necessário
if [[ ! -f "migrations_done" ]]; then
    echo "🔄 Executando migrações iniciais..."
    python manage.py migrate --run-syncdb
    touch migrations_done
fi

# Iniciar servidor
echo "🌐 Iniciando servidor Django..."
python manage.py runserver 0.0.0.0:8000
