import requests
from django.conf import settings


class ZenviaNotificador:
    """Gerenciador de envio de SMS via Zenvia"""
    
    def __init__(self):
        self.api_token = getattr(settings, 'ZENVIA_API_TOKEN', None)
        self.from_name = getattr(settings, 'ZENVIA_FROM_NAME', 'SGLI')
        self.base_url = 'https://api.zenvia.com/v2/channels/sms/messages'
        
        self.enabled = bool(self.api_token)
    
    def enviar_sms(self, para, mensagem):
        """
        Envia SMS via Zenvia
        
        Args:
            para: número no formato 5541999999999 (sem +)
            mensagem: texto do SMS
        
        Returns:
            (sucesso: bool, id ou erro: str)
        """
        if not self.enabled:
            return False, "Token Zenvia não configurado"
        
        try:
            # Limpar número
            numero_limpo = ''.join(filter(str.isdigit, para))
            if numero_limpo.startswith('55'):
                numero_limpo = numero_limpo[2:]
            
            headers = {
                'X-API-TOKEN': self.api_token,
                'Content-Type': 'application/json'
            }
            
            payload = {
                "from": self.from_name,
                "to": numero_limpo,
                "contents": [{
                    "type": "text",
                    "text": mensagem
                }]
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return True, data.get('id', 'enviado')
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
                
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
