#!/usr/bin/env python3
"""
HABITAT PRO - Correção de Permissões
Corrige permissões do usuário para acessar o admin
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgli_project.settings')
django.setup()

from core.models import Usuario

print("╔════════════════════════════════════════════════════════╗")
print("║   🔐 HABITAT PRO - Correção de Permissões            ║")
print("╚════════════════════════════════════════════════════════╝")
print()

# Listar usuários
usuarios = Usuario.objects.all()

if not usuarios.exists():
    print("❌ Nenhum usuário encontrado no sistema!")
    print()
    print("Crie um superusuário primeiro:")
    print("   python manage.py createsuperuser")
    sys.exit(1)

print("📋 Usuários encontrados:")
print()

for i, user in enumerate(usuarios, 1):
    print(f"{i}. {user.username} (Email: {user.email})")
    print(f"   Staff: {user.is_staff} | Superuser: {user.is_superuser}")
    print()

print("════════════════════════════════════════════════════════")
print()

# Perguntar qual usuário corrigir
if len(usuarios) == 1:
    usuario = usuarios[0]
    print(f"✅ Selecionando único usuário: {usuario.username}")
else:
    try:
        escolha = int(input(f"Digite o número do usuário (1-{len(usuarios)}): "))
        usuario = list(usuarios)[escolha - 1]
    except (ValueError, IndexError):
        print("❌ Escolha inválida!")
        sys.exit(1)

print()
print(f"🔧 Corrigindo permissões de: {usuario.username}")
print()

# Corrigir permissões
usuario.is_staff = True
usuario.is_superuser = True
usuario.is_active = True
usuario.save()

print("✅ Permissões atualizadas:")
print(f"   • is_staff: True")
print(f"   • is_superuser: True")
print(f"   • is_active: True")
print()

print("════════════════════════════════════════════════════════")
print("✅ CORREÇÃO CONCLUÍDA!")
print("════════════════════════════════════════════════════════")
print()
print("🔄 Reinicie o servidor Django e tente acessar o admin novamente:")
print("   python manage.py runserver 0.0.0.0:8000")
print()
