"""
Models para controle de notificações enviadas
"""
from django.db import models
from core.models import Comanda
import uuid


class NotificacaoLog(models.Model):
    """Log de notificações enviadas"""
    
    TIPO_CHOICES = [
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp'),
        ('SMS', 'SMS'),
    ]
    
    STATUS_CHOICES = [
        ('ENVIADO', 'Enviado'),
        ('ERRO', 'Erro'),
        ('PENDENTE', 'Pendente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comanda = models.ForeignKey(Comanda, on_delete=models.CASCADE, related_name='notificacoes')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    destinatario = models.CharField(max_length=200)  # Email ou telefone
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    mensagem = models.TextField(blank=True)  # Mensagem de erro ou sucesso
    data_envio = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Log de Notificação'
        verbose_name_plural = 'Logs de Notificações'
        ordering = ['-data_envio']
    
    def __str__(self):
        return f"{self.tipo} - {self.destinatario} - {self.status}"
