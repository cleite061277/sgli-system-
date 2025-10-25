# core/tests/test_rbac.py
from django.test import TestCase
from django.contrib.auth.models import Group
from core.models import Usuario
from core.rbac import (
    criar_grupos_permissoes,
    adicionar_usuario_ao_grupo,
    usuario_tem_grupo,
    usuario_pode_editar_financeiro,
    usuario_pode_deletar
)


class RBACTestCase(TestCase):
    def setUp(self):
        criar_grupos_permissoes()
        
        self.admin_user = Usuario.objects.create_user(
            username='admin_teste',
            email='admin@teste.com',
            password='senha123'
        )
        adicionar_usuario_ao_grupo(self.admin_user, 'Admin')
        
        self.gerente_user = Usuario.objects.create_user(
            username='gerente_teste',
            email='gerente@teste.com',
            password='senha123'
        )
        adicionar_usuario_ao_grupo(self.gerente_user, 'Gerente')
    
    def test_grupos_criados(self):
        self.assertTrue(Group.objects.filter(name='Admin').exists())
        self.assertTrue(Group.objects.filter(name='Gerente').exists())
        self.assertTrue(Group.objects.filter(name='Operador').exists())
        self.assertTrue(Group.objects.filter(name='Visualizador').exists())
    
    def test_usuario_tem_grupo(self):
        self.assertTrue(usuario_tem_grupo(self.admin_user, 'Admin'))
        self.assertTrue(usuario_tem_grupo(self.gerente_user, 'Gerente'))
        self.assertFalse(usuario_tem_grupo(self.gerente_user, 'Admin'))
    
    def test_usuario_pode_editar_financeiro(self):
        self.assertTrue(usuario_pode_editar_financeiro(self.admin_user))
        self.assertTrue(usuario_pode_editar_financeiro(self.gerente_user))
    
    def test_usuario_pode_deletar(self):
        self.assertTrue(usuario_pode_deletar(self.admin_user))
        self.assertFalse(usuario_pode_deletar(self.gerente_user))
