"""
════════════════════════════════════════════════════════════════════
VIEWS PÚBLICAS - CONFIRMAÇÃO DE RESCISÃO
Arquivo: core/views_rescisao.py
Descrição: Views sem autenticação para inquilino confirmar rescisão
════════════════════════════════════════════════════════════════════
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from .models_rescisao import RescisaoContrato, ComandaRescisao


# ════════════════════════════════════════════════════════════════
# VIEW: Confirmação de Rescisão (Link Público)
# ════════════════════════════════════════════════════════════════

def confirmar_rescisao_view(request, token):
    """
    View pública para inquilino confirmar rescisão via token.
    Não requer autenticação.
    """
    rescisao = get_object_or_404(RescisaoContrato, token_confirmacao=token)
    
    # Validar token
    if not rescisao.token_confirmacao_valido:
        return render(request, 'rescisao/token_expirado.html', {
            'rescisao': rescisao,
            'contato_email': 'contato@policorp.com.br',
            'contato_telefone': '(41) 3423-xxxx',
        })
    
    # Se já confirmado
    if rescisao.confirmado_por_inquilino:
        return render(request, 'rescisao/ja_confirmado.html', {
            'rescisao': rescisao,
            'data_confirmacao': rescisao.data_confirmacao_inquilino,
        })
    
    # GET: Mostrar página de confirmação
    if request.method == 'GET':
        contexto = {
            'rescisao': rescisao,
            'locacao': rescisao.locacao,
            'imovel': rescisao.locacao.imovel,
            'locatario': rescisao.locacao.locatario,
            'valores': {
                'multa': rescisao.multa_rescisoria,
                'agua': rescisao.valor_agua,
                'luz': rescisao.valor_luz,
                'condominio': rescisao.valor_condominio,
                'reparos': rescisao.custo_reparos,
                'caucao': rescisao.valor_caucao,
                'total': rescisao.valor_total_devido,
                'parcelas': rescisao.quantidade_parcelas,
                'valor_parcela': rescisao.valor_parcela,
            }
        }
        return render(request, 'rescisao/confirmar.html', contexto)
    
    # POST: Processar confirmação
    if request.method == 'POST':
        aceite_termos = request.POST.get('aceite_termos')
        
        if aceite_termos != 'sim':
            messages.error(request, 'É necessário aceitar os termos para confirmar.')
            return redirect('confirmar_rescisao', token=token)
        
        # Registrar confirmação
        rescisao.registrar_confirmacao(request)
        
        # Enviar notificações
        try:
            from core.services.email_service import EmailService
            EmailService.notificar_confirmacao_rescisao(rescisao)
        except:
            pass  # Se EmailService não estiver pronto, continua
        
        messages.success(request, 'Rescisão confirmada com sucesso!')
        return render(request, 'rescisao/confirmado_sucesso.html', {
            'rescisao': rescisao,
            'hash_confirmacao': rescisao.log_confirmacao_inquilino.get('hash_confirmacao', ''),
        })


# ════════════════════════════════════════════════════════════════
# VIEW: Visualização Pública de Comanda de Rescisão
# ════════════════════════════════════════════════════════════════

def comanda_rescisao_view(request, token_publico):
    """
    View pública para visualizar comanda de rescisão.
    SEGURANÇA:
    - Token UUID v4 (2^122 combinações - força bruta inviável)
    - Expiração obrigatória (padrão 30 dias)
    - Rate limit: bloqueia após 100 acessos ao mesmo token
    - IP real via Railway proxy headers
    - Log de tentativas inválidas
    """
    import logging
    import uuid as uuid_module
    logger = logging.getLogger(__name__)

    # Validar formato UUID antes de consultar banco
    try:
        uuid_module.UUID(str(token_publico))
    except (ValueError, AttributeError):
        logger.warning(f"Token inválido recebido: {token_publico} | IP: {_get_real_ip(request)}")
        from django.http import Http404
        raise Http404("Token inválido")

    comanda = get_object_or_404(ComandaRescisao, token_publico=token_publico)

    # IP real (Railway usa X-Forwarded-For confiável pois está atrás do proxy deles)
    ip = _get_real_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')[:200]  # Limitar tamanho

    # Rate limit: máximo 100 acessos por token
    if comanda.token_acessos >= 100:
        logger.warning(f"Rate limit atingido: token {token_publico} | IP: {ip}")
        return render(request, 'rescisao/comanda_expirada.html', {
            'comanda': comanda,
            'motivo': 'limite_acessos',
        })

    # Registrar acesso
    comanda.registrar_acesso_token(ip, user_agent)

    # Validar token (expiração)
    if not comanda.token_esta_valido:
        logger.info(f"Token expirado acessado: {token_publico} | IP: {ip}")
        return render(request, 'rescisao/comanda_expirada.html', {
            'comanda': comanda,
            'motivo': 'expirado',
        })

    contexto = {
        'comanda': comanda,
        'rescisao': comanda.rescisao,
        'locacao': comanda.rescisao.locacao,
        'imovel': comanda.rescisao.locacao.imovel,
        'locatario': comanda.get_destinatario(),
        'locador': comanda.rescisao.locacao.imovel.locador,
    }

    return render(request, 'rescisao/comanda_view.html', contexto)


def _get_real_ip(request):
    """
    Retorna IP real do cliente.
    Railway usa proxy reverso confiável — X-Forwarded-For é seguro.
    """
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        # Pegar primeiro IP da cadeia (IP real do cliente)
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')
