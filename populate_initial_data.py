#!/usr/bin/env python
"""
Popula dados iniciais necessários para o sistema funcionar
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgli_project.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

print("🔧 Populando dados iniciais...")

# Criar grupos básicos se não existirem
grupos = {
    'Administradores': 'Acesso total ao sistema',
    'Gerentes': 'Gerenciam locações e imóveis',
    'Operadores': 'Operação básica do sistema',
    'Visualizadores': 'Apenas visualização'
}

for nome_grupo, descricao in grupos.items():
    grupo, created = Group.objects.get_or_create(name=nome_grupo)
    if created:
        print(f"  ✅ Grupo '{nome_grupo}' criado")
        
        # Se for Administradores, dar todas as permissões
        if nome_grupo == 'Administradores':
            permissions = Permission.objects.all()
            grupo.permissions.set(permissions)
            print(f"     → {permissions.count()} permissões adicionadas")
    else:
        print(f"  ℹ️  Grupo '{nome_grupo}' já existe")

print("\n✅ Dados iniciais populados com sucesso!")
