"""
Dashboard widgets para monitoramento de tokens públicos
DEV_21.6 - Fase 4
"""
from django.utils import timezone
from datetime import timedelta
from core.models import Comanda, Pagamento, RenovacaoContrato
from core.utils.token_publico import token_esta_expirado, dias_ate_expirar


def get_tokens_expirando():
    """
    Retorna tokens que expiram em 7 dias ou menos.
    
    Returns:
        dict: {
            'comandas': QuerySet,
            'pagamentos': QuerySet,
            'renovacoes': QuerySet,
            'total': int
        }
    """
    agora = timezone.now()
    limite = agora + timedelta(days=7)
    
    # Comandas expirando
    comandas = Comanda.objects.filter(
        token_expira_em__lte=limite,
        token_expira_em__gte=agora
    ).select_related('locacao__locatario', 'locacao__imovel')
    
    # Pagamentos expirando
    pagamentos = Pagamento.objects.filter(
        token_expira_em__lte=limite,
        token_expira_em__gte=agora
    ).select_related('comanda__locacao__locatario')
    
    # Renovações expirando
    renovacoes = RenovacaoContrato.objects.filter(
        token_expira_em__lte=limite,
        token_expira_em__gte=agora
    ).select_related('locacao_original')
    
    return {
        'comandas': comandas,
        'pagamentos': pagamentos,
        'renovacoes': renovacoes,
        'total': comandas.count() + pagamentos.count() + renovacoes.count()
    }


def get_tokens_expirados():
    """
    Retorna tokens já expirados.
    
    Returns:
        dict: {
            'comandas': QuerySet,
            'pagamentos': QuerySet,
            'renovacoes': QuerySet,
            'total': int
        }
    """
    agora = timezone.now()
    
    # Comandas expiradas
    comandas = Comanda.objects.filter(
        token_expira_em__lt=agora
    ).select_related('locacao__locatario', 'locacao__imovel')
    
    # Pagamentos expirados
    pagamentos = Pagamento.objects.filter(
        token_expira_em__lt=agora
    ).select_related('comanda__locacao__locatario')
    
    # Renovações expiradas
    renovacoes = RenovacaoContrato.objects.filter(
        token_expira_em__lt=agora
    ).select_related('locacao_original')
    
    return {
        'comandas': comandas,
        'pagamentos': pagamentos,
        'renovacoes': renovacoes,
        'total': comandas.count() + pagamentos.count() + renovacoes.count()
    }


def get_estatisticas_tokens():
    """
    Retorna estatísticas gerais sobre tokens.
    
    Returns:
        dict: Estatísticas completas
    """
    agora = timezone.now()
    
    # Total de tokens
    total_comandas = Comanda.objects.filter(token__isnull=False).count()
    total_pagamentos = Pagamento.objects.filter(token__isnull=False).count()
    total_renovacoes = RenovacaoContrato.objects.filter(
        token_proprietario__isnull=False
    ).count()
    
    # Tokens ativos (não expirados)
    ativos_comandas = Comanda.objects.filter(
        token_expira_em__gte=agora
    ).count()
    ativos_pagamentos = Pagamento.objects.filter(
        token_expira_em__gte=agora
    ).count()
    ativos_renovacoes = RenovacaoContrato.objects.filter(
        token_expira_em__gte=agora
    ).count()
    
    # Tokens expirados
    expirados_comandas = total_comandas - ativos_comandas
    expirados_pagamentos = total_pagamentos - ativos_pagamentos
    expirados_renovacoes = total_renovacoes - ativos_renovacoes
    
    # Expirando em 7 dias
    expirando = get_tokens_expirando()
    
    return {
        'total': total_comandas + total_pagamentos + total_renovacoes,
        'ativos': ativos_comandas + ativos_pagamentos + ativos_renovacoes,
        'expirados': expirados_comandas + expirados_pagamentos + expirados_renovacoes,
        'expirando_7dias': expirando['total'],
        'por_tipo': {
            'comandas': {
                'total': total_comandas,
                'ativos': ativos_comandas,
                'expirados': expirados_comandas,
            },
            'pagamentos': {
                'total': total_pagamentos,
                'ativos': ativos_pagamentos,
                'expirados': expirados_pagamentos,
            },
            'renovacoes': {
                'total': total_renovacoes,
                'ativos': ativos_renovacoes,
                'expirados': expirados_renovacoes,
            }
        }
    }


def gerar_contexto_dashboard():
    """
    Gera contexto completo para o dashboard.
    
    Returns:
        dict: Contexto para template
    """
    return {
        'tokens_expirando': get_tokens_expirando(),
        'tokens_expirados': get_tokens_expirados(),
        'estatisticas': get_estatisticas_tokens(),
    }
