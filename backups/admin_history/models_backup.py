import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    """Modelo de usuário customizado para SGLI."""
    
    class TipoUsuario(models.TextChoices):
        ADMINISTRADOR = 'ADMIN', 'Administrador'
        GERENTE = 'MANAGER', 'Gerente'
        ATENDENTE = 'ATTENDANT', 'Atendente'
        FINANCEIRO = 'FINANCIAL', 'Financeiro'
        LOCADOR = 'LANDLORD', 'Locador'
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TipoUsuario.choices,
        default=TipoUsuario.ATENDENTE,
        verbose_name='Tipo de Usuário'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        db_table = 'core_usuario'
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_tipo_usuario_display()})"
