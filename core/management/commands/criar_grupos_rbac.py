from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from core.rbac import criar_grupos_permissoes, ROLES

class Command(BaseCommand):
    help = 'Cria grupos RBAC'
    
    def handle(self, *args, **options):
        self.stdout.write('🔐 Criando grupos RBAC...')
        criar_grupos_permissoes()
        self.stdout.write('✅ Grupos criados!')
        for role_name, role_data in ROLES.items():
            group = Group.objects.get(name=role_name)
            self.stdout.write(f"  • {role_name}: {group.permissions.count()} permissões")
