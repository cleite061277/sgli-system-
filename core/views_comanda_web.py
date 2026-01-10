"""
View para exibir comanda em página web (acesso via link do WhatsApp)
DEV_21.8.9 - FALLBACK COMPLETO para todas properties
"""
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.utils import timezone
from core.models import Comanda
import hashlib


def gerar_token_comanda(comanda_id):
    """Gera token único para acesso seguro"""
    secret = "sgli-secret-key-2024"
    return hashlib.sha256(f"{comanda_id}{secret}".encode()).hexdigest()[:16]


def validar_token_comanda(comanda_id, token):
    """Valida token de acesso"""
    return token == gerar_token_comanda(comanda_id)


def _calcular_dias_atraso_manual(comanda):
    """Fallback: Calcula dias de atraso manualmente"""
    if not comanda.data_vencimento:
        return 0
    
    hoje = timezone.now().date()
    
    # Se não venceu, não tem atraso
    if hoje <= comanda.data_vencimento:
        return 0
    
    # Se está paga ou cancelada, não tem atraso
    if comanda.status in ['PAID', 'CANCELLED']:
        return 0
    
    # Calcular dias de atraso
    return (hoje - comanda.data_vencimento).days


def _calcular_dias_vencimento_manual(comanda):
    """Fallback: Calcula dias até vencimento manualmente"""
    if not comanda.data_vencimento:
        return 0
    
    hoje = timezone.now().date()
    
    # Se já venceu, retorna 0
    if hoje >= comanda.data_vencimento:
        return 0
    
    # Calcular dias restantes
    return (comanda.data_vencimento - hoje).days


def _get_property_safe(obj, prop_name, fallback_func):
    """
    Obtém valor de property com fallback seguro
    
    Args:
        obj: Objeto do model
        prop_name: Nome da property
        fallback_func: Função para calcular manualmente
    
    Returns:
        int: Valor da property ou resultado do fallback
    """
    try:
        value = getattr(obj, prop_name)
        
        # Garantir que é int
        if not isinstance(value, int):
            raise TypeError(f"{prop_name} retornou {type(value)}, esperado int")
        
        return value
    
    except (AttributeError, TypeError) as e:
        # Log do problema (opcional, para diagnóstico)
        # print(f"⚠️ Fallback ativado para {prop_name}: {e}")
        
        # Usar fallback
        return fallback_func(obj)


def comanda_web_view(request, comanda_id, token):
    """
    Exibe comanda com design bonito (mesmo do email)
    URL: /comanda/<uuid>/<token>/
    """
    # Validar token
    if not validar_token_comanda(str(comanda_id), token):
        raise Http404("Link inválido ou expirado")
    
    # Buscar comanda
    comanda = get_object_or_404(Comanda, id=comanda_id, is_active=True)
    
    # 🛡️ OBTER PROPERTIES COM FALLBACK SEGURO
    is_vencida = _get_property_safe(
        comanda, 
        'is_vencida',
        lambda c: timezone.now().date() > c.data_vencimento if c.data_vencimento else False
    )
    
    # Aplicar multa/juros se vencida
    if is_vencida:
        comanda.aplicar_multa_juros(salvar=True)
        comanda.refresh_from_db()
    
    # 🛡️ CALCULAR dias_atraso COM FALLBACK
    dias_atraso = _get_property_safe(
        comanda,
        'dias_atraso',
        _calcular_dias_atraso_manual
    )
    
    # 🛡️ CALCULAR dias_vencimento COM FALLBACK
    dias_vencimento = _get_property_safe(
        comanda,
        'dias_vencimento',
        _calcular_dias_vencimento_manual
    )
    
    # Preparar contexto (mesmo do email)
    contexto = {
        'comanda': comanda,
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
        'tem_multa_juros': is_vencida,
        'dias_atraso': dias_atraso,
        'observacoes': comanda.observacoes,
    }
    
    # Determinar tipo de mensagem USANDO VARIÁVEIS SEGURAS
    if dias_atraso > 0:
        contexto['titulo'] = f'⚠️ PAGAMENTO EM ATRASO - {dias_atraso} dias'
        contexto['mensagem'] = f'Seu aluguel está em atraso há {dias_atraso} dias. Por favor, regularize sua situação.'
    elif dias_vencimento == 0:
        contexto['titulo'] = 'Lembrete: Vencimento HOJE'
        contexto['mensagem'] = 'Seu aluguel vence HOJE. Efetue o pagamento para evitar multa.'
    elif dias_vencimento == 1:
        contexto['titulo'] = 'Lembrete: Vencimento AMANHÃ'
        contexto['mensagem'] = 'Seu aluguel vence AMANHÃ. Por favor, efetue o pagamento.'
    else:
        contexto['titulo'] = f'Lembrete: Vencimento em {dias_vencimento} dias'
        contexto['mensagem'] = f'Seu aluguel vence em {dias_vencimento} dias.'
    
    return render(request, 'comanda/comanda_web.html', contexto)
