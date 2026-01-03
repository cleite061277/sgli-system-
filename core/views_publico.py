"""
Views públicas para Comandas e Recibos
Sistema de tokens com expiração de 30 dias
DEV_21.6 - Fase 2
"""
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.utils import timezone
from core.models import Comanda, Pagamento
from core.utils.token_publico import validar_token, dias_ate_expirar


def comanda_publica_view(request, token):
    """
    View pública para visualizar comanda via token UUID.
    Token expira em 30 dias.
    """
    # Buscar comanda pelo token
    comanda = get_object_or_404(Comanda, token=token)
    
    # Validar token
    valido, mensagem_erro = validar_token(comanda, str(token))
    
    if not valido:
        # Token inválido ou expirado
        return render(request, 'publico/token_expirado.html', {
            'tipo': 'comanda',
            'mensagem': mensagem_erro,
            'numero': comanda.numero_comanda,
        })
    
    # Token válido - montar contexto
    contexto = {
        'comanda': comanda,
        'locatario_nome': comanda.locacao.locatario.nome_razao_social,
        'imovel_endereco': f"{comanda.locacao.imovel.endereco}, {comanda.locacao.imovel.numero}",
        'numero_comanda': comanda.numero_comanda,
        'data_vencimento': comanda.data_vencimento.strftime('%d/%m/%Y'),
        'valor_aluguel': f"{comanda.valor_aluguel:,.2f}",
        'valor_condominio': f"{comanda.valor_condominio:,.2f}",
        'valor_iptu': f"{comanda.valor_iptu:,.2f}",
        'valor_total': f"{comanda.valor_total:,.2f}",
        'observacoes': comanda.observacoes,
        'dias_restantes': dias_ate_expirar(comanda),
        'tem_multa_juros': comanda.is_vencida if hasattr(comanda, 'is_vencida') else False,
    }
    
    # Determinar título/mensagem baseado no status
    if contexto['tem_multa_juros']:
        contexto['titulo'] = '⚠️ PAGAMENTO EM ATRASO'
        contexto['mensagem'] = 'Seu aluguel está em atraso. Por favor, regularize sua situação.'
    elif comanda.data_vencimento == timezone.now().date():
        contexto['titulo'] = '🔔 VENCIMENTO HOJE'
        contexto['mensagem'] = 'Seu aluguel vence hoje. Evite multas e juros!'
    else:
        contexto['titulo'] = '📋 COMANDA DE PAGAMENTO'
        contexto['mensagem'] = f'Sua comanda de aluguel referente ao imóvel {contexto["imovel_endereco"]}.'
    
    return render(request, 'publico/comanda_publica.html', contexto)


def recibo_publico_view(request, token):
    """
    View pública para visualizar recibo via token UUID.
    Token expira em 30 dias.
    """
    # Buscar pagamento pelo token
    pagamento = get_object_or_404(Pagamento, token=token)
    
    # Validar token
    valido, mensagem_erro = validar_token(pagamento, str(token))
    
    if not valido:
        # Token inválido ou expirado
        return render(request, 'publico/token_expirado.html', {
            'tipo': 'recibo',
            'mensagem': mensagem_erro,
            'numero': pagamento.numero_pagamento,
        })
    
    # Token válido - montar contexto
    contexto = {
        'pagamento': pagamento,
        'comanda': pagamento.comanda,
        'locatario_nome': pagamento.comanda.locacao.locatario.nome_razao_social,
        'imovel_endereco': f"{pagamento.comanda.locacao.imovel.endereco}, {pagamento.comanda.locacao.imovel.numero}",
        'numero_recibo': pagamento.numero_pagamento,
        'data_pagamento': pagamento.data_pagamento.strftime('%d/%m/%Y'),
        'forma_pagamento': pagamento.get_forma_pagamento_display() if hasattr(pagamento, 'get_forma_pagamento_display') else pagamento.forma_pagamento,
        'valor_pago': f"{pagamento.valor_pago:,.2f}",
        'observacoes': pagamento.comanda.observacoes if pagamento.comanda else None,
        'dias_restantes': dias_ate_expirar(pagamento),
    }
    
    return render(request, 'publico/recibo_publico.html', contexto)
