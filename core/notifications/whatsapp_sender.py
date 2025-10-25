"""
WhatsApp Sender - Envio via Twilio
"""
from twilio.rest import Client
from django.conf import settings
from .message_formatter import MessageFormatter
import logging

logger = logging.getLogger(__name__)


class WhatsAppSender:
    """Classe para envio de WhatsApp via Twilio"""
    
    def __init__(self):
        """Inicializa cliente Twilio"""
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_WHATSAPP_FROM
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
    
    def enviar_comanda(self, comanda):
        """
        Envia comanda por WhatsApp
        
        Args:
            comanda: Objeto Comanda
            
        Returns:
            tuple: (sucesso: bool, mensagem: str)
        """
        try:
            # Verificar se Twilio está configurado
            if not self.client:
                logger.warning("Twilio não configurado")
                return False, "Twilio não configurado"
            
            locatario = comanda.locacao.locatario
            
            # Verificar se locatário tem telefone
            if not locatario.telefone:
                logger.warning(f"Locatário {locatario.nome_razao_social} sem telefone")
                return False, "Locatário sem telefone cadastrado"
            
            # Formatar número para WhatsApp
            # Remove caracteres especiais e adiciona whatsapp:
            telefone = ''.join(filter(str.isdigit, locatario.telefone))
            
            # Adicionar código do país se não tiver (Brasil = 55)
            if not telefone.startswith('55'):
                telefone = '55' + telefone
            
            to_number = f'whatsapp:+{telefone}'
            
            # Preparar mensagem
            mensagem = MessageFormatter.formatar_mensagem_whatsapp(comanda)
            
            # Enviar via Twilio
            message = self.client.messages.create(
                body=mensagem,
                from_=self.from_number,
                to=to_number
            )
            
            logger.info(f"WhatsApp enviado para {to_number} - SID: {message.sid}")
            return True, f"WhatsApp enviado para {locatario.telefone}"
            
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp: {str(e)}")
            return False, f"Erro: {str(e)}"
    
    def testar_conexao(self, numero_teste=None):
        """
        Testa conexão Twilio
        
        Args:
            numero_teste: Número para teste (formato: +5511999999999)
            
        Returns:
            tuple: (sucesso: bool, mensagem: str)
        """
        try:
            if not self.client:
                return False, "Twilio não configurado"
            
            if not numero_teste:
                return False, "Informe um número de teste"
            
            # Formatar número
            telefone = ''.join(filter(str.isdigit, numero_teste))
            if not telefone.startswith('55'):
                telefone = '55' + telefone
            to_number = f'whatsapp:+{telefone}'
            
            # Enviar mensagem de teste
            message = self.client.messages.create(
                body='🧪 Teste SGLI - Configuração WhatsApp OK! ✅',
                from_=self.from_number,
                to=to_number
            )
            
            return True, f"Teste enviado! SID: {message.sid}"
            
        except Exception as e:
            return False, f"Erro: {str(e)}"
