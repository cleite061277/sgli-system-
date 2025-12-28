"""
APScheduler - Agendador de tarefas automáticas do HABITAT PRO
Executa notificações de comandas sem necessidade de Redis/Celery

JOBS CONFIGURADOS:
- Diário às 8h: Envio de todas notificações programadas
- A cada hora: Backup para vencimentos urgentes (hoje/amanhã)
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings
from django.core.management import call_command
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util
import pytz

logger = logging.getLogger(__name__)


def enviar_notificacoes_job():
    """
    Job principal: Envia todas notificações programadas
    Executa: Diariamente às 8h00
    """
    try:
        logger.info("🚀 [SCHEDULER] Iniciando job de notificações diárias...")
        call_command('enviar_notificacoes')
        logger.info("✅ [SCHEDULER] Job de notificações concluído com sucesso")
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Erro no job de notificações: {str(e)}")


def verificar_vencimentos_urgentes_job():
    """
    Job backup: Verifica vencimentos urgentes (hoje e amanhã)
    Executa: A cada hora
    Garante que notificações críticas não sejam perdidas
    """
    try:
        from datetime import date, timedelta
        from core.models import Comanda
        
        hoje = date.today()
        amanha = hoje + timedelta(days=1)
        
        # Comandas que vencem HOJE e ainda não notificadas
        urgentes_hoje = Comanda.objects.filter(
            data_vencimento=hoje,
            status__in=['PENDING', 'OVERDUE'],
            notificacao_enviada_vencimento=False,
            is_active=True
        ).count()
        
        # Comandas que vencem AMANHÃ (1 dia antes) e ainda não notificadas
        urgentes_amanha = Comanda.objects.filter(
            data_vencimento=amanha,
            status__in=['PENDING', 'OVERDUE'],
            notificacao_enviada_1dia=False,
            is_active=True
        ).count()
        
        total_urgentes = urgentes_hoje + urgentes_amanha
        
        if total_urgentes > 0:
            logger.warning(
                f"⚠️  [SCHEDULER] {total_urgentes} comandas urgentes detectadas "
                f"(Hoje: {urgentes_hoje}, Amanhã: {urgentes_amanha})"
            )
            # Executa comando para processar urgentes
            call_command('enviar_notificacoes')
        else:
            logger.info("✅ [SCHEDULER] Nenhuma comanda urgente pendente")
            
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Erro no job de vencimentos urgentes: {str(e)}")


@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    Deleta execuções antigas do job (mantém apenas últimos 7 dias)
    Previne crescimento infinito da tabela DjangoJobExecution
    """
    try:
        DjangoJobExecution.objects.delete_old_job_executions(max_age)
        logger.info("🧹 [SCHEDULER] Limpeza de execuções antigas concluída")
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Erro na limpeza: {str(e)}")


def start_scheduler():
    """
    Inicia o APScheduler com todos os jobs configurados
    Chamado automaticamente pelo CoreConfig.ready()
    """
    try:
        # Criar scheduler com jobstore Django
        scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # JOB 1: Notificações diárias às 8h
        scheduler.add_job(
            enviar_notificacoes_job,
            trigger=CronTrigger(
                hour=8,
                minute=0,
                timezone=pytz.timezone(settings.TIME_ZONE)
            ),
            id="notificacoes_diarias",
            max_instances=1,
            replace_existing=True,
            name="Enviar notificações diárias de comandas"
        )
        logger.info("✅ [SCHEDULER] Job 'notificacoes_diarias' agendado para 8h00")
        
        # JOB 2: Backup a cada hora (vencimentos urgentes)
        scheduler.add_job(
            verificar_vencimentos_urgentes_job,
            trigger=IntervalTrigger(
                hours=1,
                timezone=pytz.timezone(settings.TIME_ZONE)
            ),
            id="vencimentos_urgentes",
            max_instances=1,
            replace_existing=True,
            name="Verificar vencimentos urgentes a cada hora"
        )
        logger.info("✅ [SCHEDULER] Job 'vencimentos_urgentes' agendado (a cada 1h)")
        
        # JOB 3: Limpeza semanal de execuções antigas (todo domingo às 2h)
        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="sun",
                hour=2,
                minute=0,
                timezone=pytz.timezone(settings.TIME_ZONE)
            ),
            id="limpeza_execucoes",
            max_instances=1,
            replace_existing=True,
            name="Limpeza semanal de execuções antigas"
        )
        logger.info("✅ [SCHEDULER] Job 'limpeza_execucoes' agendado (domingos 2h)")
        
        # Iniciar scheduler
        scheduler.start()
        logger.info("🎉 [SCHEDULER] APScheduler iniciado com sucesso!")
        
        # Log dos jobs ativos
        jobs = scheduler.get_jobs()
        logger.info(f"📋 [SCHEDULER] Total de jobs ativos: {len(jobs)}")
        for job in jobs:
            logger.info(f"   • {job.id}: {job.name}")
        
        return scheduler
        
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Erro ao iniciar scheduler: {str(e)}")
        raise
    
    # ════════════════════════════════════════════════════════════════
    # JOB 4: DETECÇÃO DE RENOVAÇÕES - DEV_21
    # ════════════════════════════════════════════════════════════════
    from core.management.commands.detectar_renovacoes import Command as DetectarRenovacoesCommand
    
    scheduler.add_job(
        lambda: DetectarRenovacoesCommand().handle(dry_run=False, dias=90, aumento=0.0),
        trigger=CronTrigger(hour=8, minute=0),  # Diariamente às 8h
        id='detectar_renovacoes',
        name='Detectar Renovações de Contratos (D-90)',
        replace_existing=True,
        max_instances=1,
    )
    logger.info("✅ Job 'detectar_renovacoes' agendado: Diariamente às 08:00")

