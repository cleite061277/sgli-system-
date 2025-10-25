from django.contrib.auth.models import Group, Permission
from functools import wraps
from django.http import HttpResponseForbidden
from rest_framework.permissions import BasePermission

ROLES = {
    'Admin': {
        'description': 'Acesso total ao sistema',
        'permissions': 'all',
    },
    'Gerente': {
        'description': 'Gerencia locações, contratos e relatórios',
        'permissions': [
            'view_locador', 'add_locador', 'change_locador',
            'view_locatario', 'add_locatario', 'change_locatario',
            'view_imovel', 'add_imovel', 'change_imovel',
            'view_locacao', 'add_locacao', 'change_locacao',
            'view_templatecontrato', 'add_templatecontrato', 'change_templatecontrato',
            'view_comanda', 'add_comanda', 'change_comanda',
            'view_pagamento', 'add_pagamento', 'change_pagamento',
            'view_usuario',
        ]
    },
    'Operador': {
        'description': 'Registra pagamentos e gera documentos',
        'permissions': [
            'view_locador', 'view_locatario', 'view_imovel', 'view_locacao',
            'view_comanda', 'add_comanda',
            'view_pagamento', 'add_pagamento', 'change_pagamento',
            'view_templatecontrato',
        ]
    },
    'Visualizador': {
        'description': 'Apenas leitura de dados',
        'permissions': [
            'view_locador', 'view_locatario', 'view_imovel',
            'view_locacao', 'view_comanda', 'view_pagamento',
            'view_templatecontrato',
        ]
    }
}

def criar_grupos_permissoes():
    for role_name, role_data in ROLES.items():
        group, created = Group.objects.get_or_create(name=role_name)
        if role_data['permissions'] == 'all':
            all_permissions = Permission.objects.all()
            group.permissions.set(all_permissions)
        else:
            permissions = []
            for perm_codename in role_data['permissions']:
                try:
                    perm = Permission.objects.get(codename=perm_codename)
                    permissions.append(perm)
                except Permission.DoesNotExist:
                    print(f"⚠️  '{perm_codename}' não encontrada")
            group.permissions.set(permissions)
        status = "criado" if created else "atualizado"
        print(f"✅ Grupo '{role_name}' {status} com {group.permissions.count()} permissões")

def require_role(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Autenticação necessária")
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            user_groups = request.user.groups.values_list('name', flat=True)
            if any(role in user_groups for role in roles):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden(f"Requer: {', '.join(roles)}")
        return wrapper
    return decorator

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Admin').exists()

class IsGerenteOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name__in=['Admin', 'Gerente']).exists()

class IsOperadorOrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name__in=['Admin', 'Gerente', 'Operador']).exists()

class IsVisualizadorOrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

def usuario_tem_grupo(user, grupo_nome):
    return user.groups.filter(name=grupo_nome).exists()

def usuario_pode_editar_financeiro(user):
    return user.groups.filter(name__in=['Admin', 'Gerente']).exists()

def usuario_pode_deletar(user):
    return user.groups.filter(name='Admin').exists()

def adicionar_usuario_ao_grupo(user, grupo_nome):
    try:
        grupo = Group.objects.get(name=grupo_nome)
        user.groups.add(grupo)
        return True
    except Group.DoesNotExist:
        return False
