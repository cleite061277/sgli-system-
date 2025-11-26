"""
Correção de Encoding - NotificacaoLog
Execute este arquivo se houver problemas de encoding
"""

# Se o arquivo core/notifications/models.py tiver encoding corrompido,
# substitua o conteúdo completo por:

CONTEUDO_CORRETO = '''"""
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
'''

# INSTRUÇÕES DE USO:
# 1. Localize o arquivo: core/notifications/models.py
# 2. Substitua o conteúdo pelo texto acima
# 3. Salve com encoding UTF-8
# 4. Execute: python manage.py makemigrations
# 5. Execute: python manage.py migrate

print("✅ Conteúdo correto disponível na variável CONTEUDO_CORRETO")
print("📝 Copie e cole no arquivo core/notifications/models.py")
