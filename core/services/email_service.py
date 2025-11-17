"""
Serviço responsável pelo envio de emails de notificação.
Princípios: Single Responsibility, Testável, Reutilizável
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from core.models import LogNotificacao, Comanda
from datetime import date
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Serviço de envio de emails de notificação"""
    
    TIPOS_MENSAGEM = {
        '10D': {
            'titulo': 'Lembrete: Vencimento em 10 dias',
            'mensagem': 'Seu aluguel vence em 10 dias. Não esqueça de efetuar o pagamento.',
        },
        '7D': {
            'titulo': 'Lembrete: Vencimento em 7 dias',
            'mensagem': 'Seu aluguel vence em 7 dias. Por favor, organize o pagamento.',
        },
        '1D': {
            'titulo': 'Lembrete: Vencimento AMANHÃ',
            'mensagem': 'Seu aluguel vence AMANHÃ. Por favor, efetue o pagamento para evitar multa e juros.',
        },
        'VEN': {
            'titulo': 'Lembrete: Vencimento HOJE',
            'mensagem': 'Seu aluguel vence HOJE. Efetue o pagamento para evitar multa de 10% e juros de 1% ao mês.',
        },
        'ATR1': {
            'titulo': '⚠️ PAGAMENTO EM ATRASO',
            'mensagem': 'Seu aluguel está em atraso há 1 dia. Multa de 10% e juros já foram aplicados.',
        },
        'ATR7': {
            'titulo': '⚠️ PAGAMENTO EM ATRASO - 7 dias',
            'mensagem': 'Seu aluguel está em atraso há 7 dias. Por favor, regularize sua situação.',
        },
        'ATR14': {
            'titulo': '⚠️ PAGAMENTO EM ATRASO - 14 dias',
            'mensagem': 'Seu aluguel está em atraso há 14 dias. Entre em contato urgentemente.',
        },
        'ATR21': {
            'titulo': '⚠️ PAGAMENTO EM ATRASO - 21 dias',
            'mensagem': 'Seu aluguel está em atraso há 21 dias. Situação crítica. Entre em contato imediatamente.',
        },
    }
    
    @staticmethod
    def preparar_contexto(comanda: Comanda, tipo_notificacao: str) -> dict:
        """Prepara contexto para renderizar template"""
        
        # Aplicar multa/juros se vencida
        if comanda.is_vencida:
            comanda.aplicar_multa_juros(salvar=True)
            comanda.refresh_from_db()
        
        config = EmailService.TIPOS_MENSAGEM[tipo_notificacao]
        
        return {
            'titulo': config['titulo'],
            'mensagem_principal': config['mensagem'],
            'locatario_nome': comanda.locacao.locatario.nome_razao_social,
            'imovel_endereco': f"{comanda.locacao.imovel.endereco}, {comanda.locacao.imovel.numero}",
            'numero_comanda': comanda.numero_comanda,
            'data_vencimento': comanda.data_vencimento.strftime('%d/%m/%Y'),
            'valor_aluguel': f"{comanda.valor_aluguel:,.2f}",
            'valor_condominio': f"{comanda.valor_condominio:,.2f}",
            'valor_iptu': f"{comanda.valor_iptu:,.2f}",
            'valor_multa': f"{comanda.valor_multa:,.2f}",
            'valor_juros': f"{comanda.valor_juros:,.2f}",
            'valor_total': f"{comanda.valor_total:,.2f}",
            'tem_multa_juros': comanda.is_vencida,
            'dias_atraso': comanda.dias_atraso if comanda.is_vencida else 0,
            'link_pagamento': f"http://localhost:8000/admin/core/comanda/{comanda.id}/change/",
        }
    
    @classmethod
    def enviar_notificacao(cls, comanda: Comanda, tipo_notificacao: str) -> bool:
        """
        Envia email de notificação para locatário
        """
        try:
            # Validações
            if not comanda.locacao.locatario.email:
                logger.warning(f"Comanda {comanda.numero_comanda}: Locatário sem email")
                return False
            
            # Preparar contexto
            contexto = cls.preparar_contexto(comanda, tipo_notificacao)
            
            # Renderizar templates
            html_content = render_to_string('emails/lembrete_vencimento.html', contexto)
            text_content = render_to_string('emails/lembrete_vencimento.txt', contexto)
            
            # Criar email
            email = EmailMultiAlternatives(
                subject=contexto['titulo'],
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[comanda.locacao.locatario.email],
            )
            email.attach_alternative(html_content, "text/html")
            
            # Enviar
            email.send()
            
            # Registrar log
            LogNotificacao.objects.create(
                comanda=comanda,
                tipo_notificacao=tipo_notificacao,
                destinatario_email=comanda.locacao.locatario.email,
                sucesso=True
            )
            
            logger.info(f"✅ Email enviado: {tipo_notificacao} - {comanda.numero_comanda}")
            return True
            
        except Exception as e:
            LogNotificacao.objects.create(
                comanda=comanda,
                tipo_notificacao=tipo_notificacao,
                destinatario_email=comanda.locacao.locatario.email or 'sem_email@erro.com',
                sucesso=False,
                mensagem_erro=str(e)
            )
            
            logger.error(f"❌ Erro ao enviar email: {comanda.numero_comanda} - {e}")
            return False
