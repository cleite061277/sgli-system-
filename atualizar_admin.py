#!/usr/bin/env python3
"""
Script para atualizar admin.py automaticamente
"""

import re
import shutil
from datetime import datetime

def backup_admin():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy('core/admin.py', f'core/admin.py.backup_admin_{timestamp}')
    print(f"✅ Backup criado: core/admin.py.backup_admin_{timestamp}")

def main():
    print("=" * 70)
    print("🔧 ATUALIZAÇÃO AUTOMÁTICA DO ADMIN.PY")
    print("=" * 70)
    print()
    
    backup_admin()
    print()
    
    with open('core/admin.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Verificar se Fiador já está nos imports
    imports_updated = False
    for i, line in enumerate(lines):
        if 'from .models import' in line and 'Fiador' not in line:
            # Adicionar Fiador aos imports
            lines[i] = line.replace('from .models import', 'from .models import Fiador,')
            imports_updated = True
            break
    
    if imports_updated:
        print("✅ Import de Fiador adicionado")
    
    # Salvar
    with open('core/admin.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    # Adicionar FiadorAdmin no final do arquivo
    fiador_admin = '''

# ===========================================================================
# ADMIN FIADOR
# ===========================================================================

@admin.register(Fiador)
class FiadorAdmin(admin.ModelAdmin):
    """Admin para Fiador."""
    
    list_display = ['nome_completo', 'cpf', 'telefone', 'empresa_trabalho', 'created_at']
    list_filter = ['created_at', 'is_active']
    search_fields = ['nome_completo', 'cpf', 'rg', 'email', 'telefone']
    
    fieldsets = (
        ('📋 Dados Pessoais', {
            'fields': ('nome_completo', 'cpf', 'rg', 'data_nascimento')
        }),
        ('👨‍👩‍👦 Filiação', {
            'fields': ('nome_pai', 'nome_mae'),
            'classes': ['collapse'],
        }),
        ('📞 Contatos', {
            'fields': ('telefone', 'email', 'outro_telefone', ('nome_contato_emergencia', 'telefone_contato_emergencia'))
        }),
        ('🏠 Endereço', {
            'fields': ('endereco_completo', 'cep')
        }),
        ('💼 Dados Profissionais', {
            'fields': ('empresa_trabalho', 'endereco_empresa', 'telefone_empresa', 'contato_empresa', 'tempo_empresa', 'renda_mensal')
        }),
        ('🕐 Metadados', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ['collapse'],
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
'''
    
    # Verificar se já existe
    with open('core/admin.py', 'r') as f:
        content = f.read()
    
    if 'class FiadorAdmin' not in content:
        with open('core/admin.py', 'a') as f:
            f.write(fiador_admin)
        print("✅ FiadorAdmin adicionado")
    else:
        print("ℹ️  FiadorAdmin já existe")
    
    print()
    print("=" * 70)
    print("✅ ADMIN.PY ATUALIZADO!")
    print("=" * 70)
    print()
    print("📋 Próximos passos:")
    print("   python -m py_compile core/admin.py")
    print("   python manage.py runserver")

if __name__ == '__main__':
    main()
