#!/bin/bash
# Comandos úteis do Sistema SGLI

echo "=== Sistema SGLI - Comandos Úteis ==="

# Iniciar servidor
alias sgli-start='python manage.py runserver'

# Migrations
alias sgli-migrate='python manage.py makemigrations && python manage.py migrate'

# Shell
alias sgli-shell='python manage.py shell'

echo "Servidor: python manage.py runserver"
echo "Migrations: python manage.py makemigrations && migrate"
echo "Admin: http://localhost:8000/admin/"
echo "Dashboard: http://localhost:8000/dashboard/financeiro/"
