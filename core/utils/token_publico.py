"""
Sistema centralizado de tokens públicos com expiração.

Implementa tokens UUID únicos com validade de 30 dias para:
- Comandas de pagamento
- Recibos de pagamento  
- Renovações de contrato

Criado em: DEV_21.6
"""
import uuid
from datetime import timedelta
from django.utils import timezone
from django.conf import settings


# Constante global de validade
VALIDADE_TOKEN_DIAS = 30


def gerar_token_publico():
    """
    Gera token UUID único.
    
    Returns:
        UUID: Token único
    """
    return uuid.uuid4()


def gerar_dados_token():
    """
    Gera token + timestamps de criação e expiração.
    
    Returns:
        dict: {
            'token': UUID,
            'token_gerado_em': datetime,
            'token_expira_em': datetime
        }
    """
    agora = timezone.now()
    expiracao = agora + timedelta(days=VALIDADE_TOKEN_DIAS)
    
    return {
        'token': gerar_token_publico(),
        'token_gerado_em': agora,
        'token_expira_em': expiracao,
    }


def validar_token(obj, token_fornecido):
    """
    Valida se token é válido e não expirou.
    
    Args:
        obj: Objeto com campos token, token_expira_em
        token_fornecido: UUID fornecido na URL
        
    Returns:
        tuple: (bool válido, str mensagem_erro)
    """
    # Verificar se token existe
    if not hasattr(obj, 'token'):
        return False, "Token não configurado"
    
    # Verificar se token bate
    if str(obj.token) != str(token_fornecido):
        return False, "Token inválido"
    
    # Verificar se não expirou
    if not hasattr(obj, 'token_expira_em'):
        return True, ""  # Sem expiração = sempre válido
    
    if obj.token_expira_em and timezone.now() > obj.token_expira_em:
        return False, "Link expirado"
    
    return True, ""


def token_esta_expirado(obj):
    """
    Verifica se token do objeto expirou.
    
    Args:
        obj: Objeto com campo token_expira_em
        
    Returns:
        bool: True se expirado, False caso contrário
    """
    if not hasattr(obj, 'token_expira_em') or not obj.token_expira_em:
        return False
    
    return timezone.now() > obj.token_expira_em


def dias_ate_expirar(obj):
    """
    Calcula quantos dias faltam para token expirar.
    
    Args:
        obj: Objeto com campo token_expira_em
        
    Returns:
        int: Dias até expirar (negativo se já expirou)
    """
    if not hasattr(obj, 'token_expira_em') or not obj.token_expira_em:
        return 999  # Sem expiração
    
    delta = obj.token_expira_em - timezone.now()
    return delta.days


def renovar_token(obj, salvar=True):
    """
    Renova token do objeto (gera novo token + nova expiração).
    
    Args:
        obj: Objeto a ter token renovado
        salvar: Se deve salvar no banco
        
    Returns:
        obj: Objeto atualizado
    """
    dados = gerar_dados_token()
    
    obj.token = dados['token']
    obj.token_gerado_em = dados['token_gerado_em']
    obj.token_expira_em = dados['token_expira_em']
    
    if salvar:
        obj.save(update_fields=['token', 'token_gerado_em', 'token_expira_em'])
    
    return obj


def gerar_url_publica(obj, tipo):
    """
    Gera URL pública completa para o objeto.
    
    Args:
        obj: Objeto com token (Comanda, Pagamento, ou RenovacaoContrato)
        tipo: 'comanda', 'recibo', 'renovacao_proprietario' ou 'renovacao_locatario'
        
    Returns:
        str: URL completa
    """
    base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    # Determinar caminho baseado no tipo
    if tipo == 'comanda':
        if not hasattr(obj, 'token'):
            raise ValueError("Objeto não possui campo 'token'")
        caminho = f'/comanda/{obj.token}/'
    
    elif tipo == 'recibo':
        if not hasattr(obj, 'token'):
            raise ValueError("Objeto não possui campo 'token'")
        caminho = f'/recibo/{obj.token}/'
    
    elif tipo == 'renovacao_proprietario':
        if not hasattr(obj, 'token_proprietario'):
            raise ValueError("Objeto não possui campo 'token_proprietario'")
        caminho = f'/renovacao/proprietario/{obj.token_proprietario}/'
    
    elif tipo == 'renovacao_locatario':
        if not hasattr(obj, 'token_locatario'):
            raise ValueError("Objeto não possui campo 'token_locatario'")
        caminho = f'/renovacao/locatario/{obj.token_locatario}/'
    
    else:
        raise ValueError(f"Tipo '{tipo}' não reconhecido. Use: comanda, recibo, renovacao_proprietario, renovacao_locatario")
    
    return f"{base_url}{caminho}"
