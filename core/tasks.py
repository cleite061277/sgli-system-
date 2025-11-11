"""
Tasks assíncronas do Celery para notificações
"""
from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from core.models import Comanda
from core.services.email_service import EmailService
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name='core.tasks.enviar_notificacoes_task')
def enviar_notificacoes_task():
    """
    Task principal: envia todas as notificações diárias
    Agendada para rodar às 8h todos os dias
    """
    logger.info("🚀 Iniciando task de envio de notificações")
    
    try:
        call_command('enviar_notificacoes')
        logger.info("✅ Task de notificações concluída com sucesso")
        return {'status': 'success', 'timestamp': timezone.now().isoformat()}
    except Exception as e:
        logger.error(f"❌ Erro na task de notificações: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task(name='core.tasks.verificar_vencimentos_urgentes_task')
def verificar_vencimentos_urgentes_task():
    """
    Task de backup: verifica vencimentos urgentes (hoje e amanhã)
    Roda a cada hora como rede de segurança
    """
    logger.info("🔍 Verificando vencimentos urgentes")
    
    hoje = date.today()
    amanha = hoje + timedelta(days=1)
    enviados = 0
    
    try:
        # Comandas que vencem hoje
        comandas_hoje = Comanda.objects.filter(
            data_vencimento=hoje,
            status__in=['PENDING', 'OVERDUE'],
            notificacao_enviada_vencimento=False,
            is_active=True
        )
        
        for comanda in comandas_hoje:
            if EmailService.enviar_notificacao(comanda, 'VEN'):
                comanda.notificacao_enviada_vencimento = True
                comanda.save(update_fields=['notificacao_enviada_vencimento', 'updated_at'])
                enviados += 1
        
        # Comandas que vencem amanhã
        comandas_amanha = Comanda.objects.filter(
            data_vencimento=amanha,
            status__in=['PENDING', 'OVERDUE'],
            notificacao_enviada_1dia=False,
            is_active=True
        )
        
        for comanda in comandas_amanha:
            if EmailService.enviar_notificacao(comanda, '1D'):
                comanda.notificacao_enviada_1dia = True
                comanda.save(update_fields=['notificacao_enviada_1dia', 'updated_at'])
                enviados += 1
        
        logger.info(f"✅ Verificação urgente concluída: {enviados} notificações enviadas")
        return {'status': 'success', 'enviados': enviados}
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação urgente: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task(name='core.tasks.enviar_notificacao_individual_task')
def enviar_notificacao_individual_task(comanda_id, tipo_notificacao):
    """
    Task para envio individual (útil para testes ou envios manuais)
    """
    try:
        comanda = Comanda.objects.get(id=comanda_id)
        sucesso = EmailService.enviar_notificacao(comanda, tipo_notificacao)
        
        return {
            'status': 'success' if sucesso else 'failed',
            'comanda': comanda.numero_comanda,
            'tipo': tipo_notificacao
        }
    except Comanda.DoesNotExist:
        logger.error(f"Comanda {comanda_id} não encontrada")
        return {'status': 'error', 'error': 'Comanda não encontrada'}
    except Exception as e:
        logger.error(f"Erro ao enviar notificação individual: {e}")
        return {'status': 'error', 'error': str(e)}
