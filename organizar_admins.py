#!/usr/bin/env python3
"""
Script para organizar todos os Admins automaticamente
"""

import re
import shutil
from datetime import datetime

def backup_admin():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy('core/admin.py', f'core/admin.py.backup_org_{timestamp}')
    print(f"✅ Backup criado: core/admin.py.backup_org_{timestamp}")

def substituir_classe(content, nome_classe, novo_codigo):
    """Substitui uma classe Admin por uma nova versão"""
    
    # Padrão para encontrar a classe e seu decorador
    padrao = rf'(@admin\.register\({nome_classe}\)[^\n]*\n)?class {nome_classe}Admin\(.*?\):\s*\n(.*?)(?=\n@admin\.register|\nclass \w+Admin|\Z)'
    
    # Procurar a classe
    match = re.search(padrao, content, re.DOTALL)
    
    if match:
        # Substituir
        content = content[:match.start()] + novo_codigo + content[match.end():]
        print(f"✅ {nome_classe}Admin substituído")
        return content, True
    else:
        print(f"⚠️  {nome_classe}Admin não encontrado")
        return content, False

def main():
    print("=" * 70)
    print("🔧 ORGANIZANDO TODOS OS ADMINS")
    print("=" * 70)
    print()
    
    # Backup
    backup_admin()
    print()
    
    # Ler arquivo
    with open('core/admin.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # USUARIO ADMIN
    usuario_admin = '''@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    """Admin organizado para Usuario"""
    
    list_display = ['username', 'get_full_name', 'email', 'tipo_usuario', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['tipo_usuario', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'cpf']
    
    fieldsets = (
        ('🔐 Autenticação', {
            'fields': ('username', 'password')
        }),
        ('👤 Dados Pessoais', {
            'fields': ('first_name', 'last_name', 'email', 'cpf', 'telefone', 'avatar')
        }),
        ('🎭 Perfil do Sistema', {
            'fields': ('tipo_usuario',)
        }),
        ('🔑 Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ['collapse'],
        }),
        ('📅 Datas Importantes', {
            'fields': ('date_joined', 'last_login'),
            'classes': ['collapse'],
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']


'''
    
    # IMOVEL ADMIN
    imovel_admin = '''@admin.register(Imovel)
class ImovelAdmin(admin.ModelAdmin):
    """Admin organizado para Imóvel"""
    
    list_display = ['codigo_imovel', 'tipo_imovel', 'status', 'endereco', 'cidade', 'valor_aluguel', 'locador', 'is_active']
    list_filter = ['tipo_imovel', 'status', 'cidade', 'estado', 'is_active', 'created_at']
    search_fields = ['codigo_imovel', 'endereco', 'bairro', 'cidade', 'locador__nome_razao_social']
    
    fieldsets = (
        ('📋 Informações Básicas', {
            'fields': ('locador', 'codigo_imovel', 'tipo_imovel', 'status')
        }),
        ('📍 Endereço', {
            'fields': ('endereco', 'numero', 'bairro', 'cidade', 'estado', 'cep')
        }),
        ('📏 Características', {
            'fields': ('area_total', 'quartos', 'banheiros')
        }),
        ('💰 Valores', {
            'fields': ('valor_aluguel', 'valor_condominio')
        }),
        ('⚡ Utilidades / Contas', {
            'fields': ('conta_agua_esgoto', 'numero_hidrometro', 'unidade_consumidora_energia'),
            'description': 'Informações de contas de consumo do imóvel'
        }),
        ('📝 Descrição', {
            'fields': ('descricao',),
            'classes': ['collapse'],
        }),
        ('🕐 Metadados', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ['collapse'],
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


'''
    
    # LOCATARIO ADMIN
    locatario_admin = '''@admin.register(Locatario)
class LocatarioAdmin(admin.ModelAdmin):
    """Admin organizado para Locatário"""
    
    list_display = ['nome_razao_social', 'cpf_cnpj', 'telefone', 'email', 'empresa_trabalho', 'tem_fiador', 'is_active']
    list_filter = ['created_at', 'is_active']
    search_fields = ['nome_razao_social', 'cpf_cnpj', 'rg', 'email', 'telefone', 'empresa_trabalho']
    
    fieldsets = (
        ('📋 Dados Pessoais', {
            'fields': ('nome_razao_social', 'cpf_cnpj', 'rg', 'data_nascimento')
        }),
        ('👨‍👩‍👦 Filiação', {
            'fields': ('nome_pai', 'nome_mae'),
            'classes': ['collapse'],
        }),
        ('📞 Contatos', {
            'fields': ('telefone', 'email', 'outro_telefone', ('nome_contato_emergencia', 'telefone_contato_emergencia'))
        }),
        ('🏠 Endereço', {
            'fields': ('endereco_completo',)
        }),
        ('💼 Dados Profissionais', {
            'fields': ('empresa_trabalho', 'endereco_empresa', 'telefone_empresa', 'contato_empresa', 'tempo_empresa', 'renda_mensal')
        }),
        ('🛡️ Garantia', {
            'fields': ('fiador',),
            'description': 'Selecione um fiador cadastrado ou deixe em branco se não houver'
        }),
        ('🕐 Metadados', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ['collapse'],
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    @admin.display(description='Fiador', boolean=True)
    def tem_fiador(self, obj):
        return obj.fiador is not None


'''
    
    # Aplicar substituições
    print("📝 Aplicando substituições...")
    print()
    
    content, _ = substituir_classe(content, 'Usuario', usuario_admin)
    content, _ = substituir_classe(content, 'Imovel', imovel_admin)
    content, _ = substituir_classe(content, 'Locatario', locatario_admin)
    
    # Salvar
    with open('core/admin.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print()
    print("=" * 70)
    print("✅ TODOS OS ADMINS ORGANIZADOS COM SUCESSO!")
    print("=" * 70)
    print()
    print("📋 Próximos passos:")
    print("   1. python -m py_compile core/admin.py")
    print("   2. python manage.py runserver")
    print("   3. Acessar: http://localhost:8000/admin/")
    print()

if __name__ == '__main__':
    main()
