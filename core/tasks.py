"""
Tarefas Agendadas - Django-Q
Envio automático de lembretes de vencimento
"""
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, date
from core.models import Comanda
from core.notifications import EmailSender, WhatsAppSender, NotificacaoLog
import logging

logger = logging.getLogger(__name__)


def enviar_lembretes_vencimento():
    """
    Tarefa agendada: Envia lembretes de vencimento
    Executa diariamente e envia para comandas que vencem em X dias
    """
    logger.info("=" * 50)
    logger.info("INICIANDO ENVIO DE LEMBRETES")
    logger.info("=" * 50)
    
    # Verificar se notificações estão ativas
    if not settings.NOTIFICACOES_ATIVAS:
        logger.info("Notificações desativadas. Abortando.")
        return {
            'status': 'desativado',
            'mensagem': 'Notificações estão desativadas no .env'
        }
    
    # Calcular data alvo (hoje + X dias)
    dias_antecedencia = settings.DIAS_ANTECEDENCIA_LEMBRETE
    data_alvo = date.today() + timedelta(days=dias_antecedencia)
    
    logger.info(f"Buscando comandas que vencem em {data_alvo.strftime('%d/%m/%Y')}")
    logger.info(f"({dias_antecedencia} dias de antecedência)")
    
    # Buscar comandas que vencem na data alvo e estão pendentes
    comandas = Comanda.objects.filter(
        data_vencimento=data_alvo,
        status='PENDENTE'
    ).select_related('locacao', 'locacao__imovel', 'locacao__locatario')
    
    total_comandas = comandas.count()
    logger.info(f"Encontradas {total_comandas} comandas para notificar")
    
    if total_comandas == 0:
        logger.info("Nenhuma comanda encontrada. Finalizando.")
        return {
            'status': 'ok',
            'total': 0,
            'enviados': 0,
            'mensagem': 'Nenhuma comanda para notificar hoje'
        }
    
    # Contadores
    emails_enviados = 0
    whatsapp_enviados = 0
    erros = 0
    
    # Inicializar senders
    email_sender = EmailSender()
    whatsapp_sender = WhatsAppSender()
    
    # Processar cada comanda
    for comanda in comandas:
        locatario = comanda.locacao.locatario
        logger.info(f"\n--- Processando Comanda #{comanda.id} ---")
        logger.info(f"Locatário: {locatario.nome_razao_social}")
        
        # Enviar Email
        if settings.ENVIAR_EMAIL:
            logger.info("Enviando email...")
            sucesso, mensagem = email_sender.enviar_comanda(comanda)
            
            # Registrar log
            NotificacaoLog.objects.create(
                comanda=comanda,
                tipo='EMAIL',
                destinatario=locatario.email or 'N/A',
                status='ENVIADO' if sucesso else 'ERRO',
                mensagem=mensagem
            )
            
            if sucesso:
                emails_enviados += 1
                logger.info(f"✅ Email: {mensagem}")
            else:
                erros += 1
                logger.error(f"❌ Email: {mensagem}")
        
        # Enviar WhatsApp
        if settings.ENVIAR_WHATSAPP:
            logger.info("Enviando WhatsApp...")
            sucesso, mensagem = whatsapp_sender.enviar_comanda(comanda)
            
            # Registrar log
            NotificacaoLog.objects.create(
                comanda=comanda,
                tipo='WHATSAPP',
                destinatario=locatario.telefone or 'N/A',
                status='ENVIADO' if sucesso else 'ERRO',
                mensagem=mensagem
            )
            
            if sucesso:
                whatsapp_enviados += 1
                logger.info(f"✅ WhatsApp: {mensagem}")
            else:
                erros += 1
                logger.error(f"❌ WhatsApp: {mensagem}")
    
    # Resumo
    logger.info("\n" + "=" * 50)
    logger.info("RESUMO DO ENVIO")
    logger.info("=" * 50)
    logger.info(f"Total de comandas: {total_comandas}")
    logger.info(f"Emails enviados: {emails_enviados}")
    logger.info(f"WhatsApp enviados: {whatsapp_enviados}")
    logger.info(f"Erros: {erros}")
    logger.info("=" * 50)
    
    return {
        'status': 'ok',
        'total': total_comandas,
        'emails': emails_enviados,
        'whatsapp': whatsapp_enviados,
        'erros': erros,
        'data_alvo': data_alvo.strftime('%d/%m/%Y')
    }


def enviar_lembrete_manual(comanda_id):
    """
    Envia lembrete manualmente para uma comanda específica
    
    Args:
        comanda_id: UUID da comanda
        
    Returns:
        dict: Resultado do envio
    """
    try:
        comanda = Comanda.objects.get(id=comanda_id)
        
        email_sender = EmailSender()
        whatsapp_sender = WhatsAppSender()
        
        resultados = {
            'comanda_id': str(comanda_id),
            'locatario': comanda.locacao.locatario.nome_razao_social,
        }
        
        # Enviar Email
        if settings.ENVIAR_EMAIL:
            sucesso, mensagem = email_sender.enviar_comanda(comanda)
            resultados['email'] = {'sucesso': sucesso, 'mensagem': mensagem}
            
            NotificacaoLog.objects.create(
                comanda=comanda,
                tipo='EMAIL',
                destinatario=comanda.locacao.locatario.email or 'N/A',
                status='ENVIADO' if sucesso else 'ERRO',
                mensagem=mensagem
            )
        
        # Enviar WhatsApp
        if settings.ENVIAR_WHATSAPP:
            sucesso, mensagem = whatsapp_sender.enviar_comanda(comanda)
            resultados['whatsapp'] = {'sucesso': sucesso, 'mensagem': mensagem}
            
            NotificacaoLog.objects.create(
                comanda=comanda,
                tipo='WHATSAPP',
                destinatario=comanda.locacao.locatario.telefone or 'N/A',
                status='ENVIADO' if sucesso else 'ERRO',
                mensagem=mensagem
            )
        
        return resultados
        
    except Comanda.DoesNotExist:
        return {
            'erro': f'Comanda {comanda_id} não encontrada'
        }
    except Exception as e:
        return {
            'erro': str(e)
        }
