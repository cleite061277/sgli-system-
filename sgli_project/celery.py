"""
Configuração do Celery para tarefas assíncronas
"""
import os
from celery import Celery
from celery.schedules import crontab

# Define o settings module do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgli_project.settings')

app = Celery('sgli_project')

# Carrega configurações do Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobre tasks automaticamente
app.autodiscover_tasks()

# Configuração do Celery Beat (agendamento)
app.conf.beat_schedule = {
    # Rodar todos os dias às 8h
    'enviar-notificacoes-diarias': {
        'task': 'core.tasks.enviar_notificacoes_task',
        'schedule': crontab(hour=8, minute=0),  # 08:00 todos os dias
        'options': {'queue': 'default'}
    },
    # Rodar a cada hora (backup)
    'verificar-vencimentos-urgentes': {
        'task': 'core.tasks.verificar_vencimentos_urgentes_task',
        'schedule': crontab(minute=0),  # Todo início de hora
        'options': {'queue': 'default'}
    },
}

# Timezone
app.conf.timezone = 'America/Sao_Paulo'

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
