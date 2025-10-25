"""
Email Sender - Envio de emails com anexos
"""
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .message_formatter import MessageFormatter
import logging

logger = logging.getLogger(__name__)


class EmailSender:
    """Classe para envio de emails"""
    
    @staticmethod
    def enviar_comanda(comanda):
        """
        Envia comanda por email
        
        Args:
            comanda: Objeto Comanda
            
        Returns:
            tuple: (sucesso: bool, mensagem: str)
        """
        try:
            locatario = comanda.locacao.locatario
            
            # Verificar se locatário tem email
            if not locatario.email:
                logger.warning(f"Locatário {locatario.nome_razao_social} sem email")
                return False, "Locatário sem email cadastrado"
            
            # Preparar assunto
            dias_restantes = (comanda.data_vencimento - comanda.mes_referencia.today()).days
            if dias_restantes > 5:
                emoji = "⏰"
                tipo = "Lembrete"
            elif dias_restantes > 0:
                emoji = "⚠️"
                tipo = "Atenção"
            else:
                emoji = "🚨"
                tipo = "URGENTE"
            
            assunto = f"{emoji} {tipo}: Aluguel vence em {dias_restantes} dias"
            if dias_restantes <= 0:
                assunto = f"{emoji} {tipo}: Aluguel vencido!"
            
            # Preparar mensagens
            html_content = MessageFormatter.formatar_email_html(comanda)
            text_content = MessageFormatter.formatar_email_texto(comanda)
            
            # Criar email
            email = EmailMultiAlternatives(
                subject=assunto,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[locatario.email],
            )
            
            # Anexar versão HTML
            email.attach_alternative(html_content, "text/html")
            
            # Enviar
            email.send(fail_silently=False)
            
            logger.info(f"Email enviado para {locatario.email} - Comanda {comanda.id}")
            return True, f"Email enviado para {locatario.email}"
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {str(e)}")
            return False, f"Erro: {str(e)}"
    
    @staticmethod
    def testar_conexao():
        """
        Testa conexão SMTP
        
        Returns:
            tuple: (sucesso: bool, mensagem: str)
        """
        try:
            from django.core.mail import send_mail
            
            send_mail(
                'Teste SGLI - Configuração de Email',
                'Se você recebeu este email, a configuração está correta!',
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            
            return True, "Email de teste enviado com sucesso!"
            
        except Exception as e:
            return False, f"Erro na configuração: {str(e)}"
