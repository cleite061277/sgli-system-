"""
View para exibir comanda em página web (acesso via link do WhatsApp)
"""
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from core.models import Comanda
import hashlib


def gerar_token_comanda(comanda_id):
    """Gera token único para acesso seguro"""
    secret = "sgli-secret-key-2024"  # Mude para algo mais seguro
    return hashlib.sha256(f"{comanda_id}{secret}".encode()).hexdigest()[:16]


def validar_token_comanda(comanda_id, token):
    """Valida token de acesso"""
    return token == gerar_token_comanda(comanda_id)


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
    
    # Aplicar multa/juros se vencida
    if comanda.is_vencida:
        comanda.aplicar_multa_juros(salvar=True)
        comanda.refresh_from_db()
    
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
        'tem_multa_juros': comanda.is_vencida,
        'dias_atraso': comanda.dias_atraso if comanda.is_vencida else 0,
    }
    
    # Determinar tipo de mensagem
    if comanda.dias_atraso > 0:
        contexto['titulo'] = f'⚠️ PAGAMENTO EM ATRASO - {comanda.dias_atraso} dias'
        contexto['mensagem'] = f'Seu aluguel está em atraso há {comanda.dias_atraso} dias. Por favor, regularize sua situação.'
    elif comanda.dias_vencimento == 0:
        contexto['titulo'] = 'Lembrete: Vencimento HOJE'
        contexto['mensagem'] = 'Seu aluguel vence HOJE. Efetue o pagamento para evitar multa.'
    elif comanda.dias_vencimento == 1:
        contexto['titulo'] = 'Lembrete: Vencimento AMANHÃ'
        contexto['mensagem'] = 'Seu aluguel vence AMANHÃ. Por favor, efetue o pagamento.'
    else:
        contexto['titulo'] = f'Lembrete: Vencimento em {comanda.dias_vencimento} dias'
        contexto['mensagem'] = f'Seu aluguel vence em {comanda.dias_vencimento} dias.'
    
    return render(request, 'comanda/comanda_web.html', contexto)
