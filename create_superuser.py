#!/usr/bin/env python
"""
Script para criar superusuário automaticamente no Railway
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgli_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Credenciais do superusuário (pegue das variáveis de ambiente)
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@sgli.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

# Verificar se já existe
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f'✅ Superusuário "{username}" criado com sucesso!')
else:
    print(f'⚠️  Superusuário "{username}" já existe.')
