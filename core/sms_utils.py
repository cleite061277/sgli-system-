from twilio.rest import Client
from django.conf import settings


class SMSNotificador:
    """Gerenciador de envio de SMS via Twilio"""
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
        
        if all([self.account_sid, self.auth_token, self.from_number]):
            self.client = Client(self.account_sid, self.auth_token)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
    
    def enviar_sms(self, para, mensagem):
        """
        Envia SMS via Twilio
        
        Args:
            para: número no formato +5541999999999
            mensagem: texto do SMS (max 160 caracteres)
        
        Returns:
            (sucesso: bool, sid ou erro: str)
        """
        if not self.enabled:
            return False, "Configuração Twilio incompleta"
        
        try:
            # Formatar número brasileiro
            if not para.startswith('+'):
                # Remove caracteres não numéricos
                numero_limpo = ''.join(filter(str.isdigit, para))
                # Adiciona código do país
                para = f"+55{numero_limpo}"
            
            message = self.client.messages.create(
                body=mensagem,
                from_=self.from_number,
                to=para
            )
            
            return True, message.sid
            
        except Exception as e:
            return False, str(e)
    
    def enviar_notificacao_vencimento(self, comanda, dias):
        """Envia notificação de vencimento próximo"""
        telefone = comanda.locacao.locatario.telefone
        
        mensagem = (
            f"SGLI - Lembrete:\n"
            f"Comanda {comanda.numero_comanda} vence em {dias} dia(s).\n"
            f"Valor: R$ {comanda.valor_total:.2f}\n"
            f"Vencimento: {comanda.data_vencimento.strftime('%d/%m/%Y')}"
        )
        
        return self.enviar_sms(telefone, mensagem)
    
    def enviar_notificacao_atraso(self, comanda, dias_atraso):
        """Envia notificação de atraso"""
        telefone = comanda.locacao.locatario.telefone
        
        mensagem = (
            f"SGLI - ATRASO:\n"
            f"Comanda {comanda.numero_comanda} vencida há {dias_atraso} dia(s).\n"
            f"Valor atualizado: R$ {comanda.valor_total:.2f}\n"
            f"(Multa + Juros inclusos)"
        )
        
        return self.enviar_sms(telefone, mensagem)
