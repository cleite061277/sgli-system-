from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from core.models import ContratoDownloadToken
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def download_contrato_token(request, token):
    """Download seguro de contrato via token UUID"""
    
    # Validar token
    try:
        token_obj = get_object_or_404(ContratoDownloadToken, token=token)
    except Exception as e:
        logger.error(f"Token não encontrado: {token}")
        return render(request, 'contratos/token_invalido.html', status=404)
    
    # Verificar expiração
    if token_obj.esta_expirado:
        logger.warning(f"Token expirado: {token}")
        context = {
            'token': token_obj,
            'renovacao': token_obj.renovacao,
            'dias_expirado': (timezone.now() - token_obj.expira_em).days,
        }
        return render(request, 'contratos/token_expirado.html', context, status=410)
    
    # Gerar PDF on-demand
    try:
        logger.info(f"Gerando PDF para token {token}")
        pdf_io = token_obj.gerar_pdf_on_demand()
        if not pdf_io:
            raise Exception("Falha ao gerar PDF")
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {e}", exc_info=True)
        context = {'erro': str(e), 'token': token_obj}
        return render(request, 'contratos/erro_geracao.html', context, status=500)
    
    # Registrar acesso
    try:
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:200]
        token_obj.registrar_acesso(ip_address=ip_address, user_agent=user_agent)
        logger.info(f"Download realizado - Token: {token} - IP: {ip_address}")
    except Exception as e:
        logger.error(f"Erro ao registrar acesso: {e}")
    
    # Retornar PDF
    try:
        numero_contrato = token_obj.renovacao.nova_locacao.numero_contrato
        filename = f'Contrato_Renovacao_{numero_contrato}.pdf'
        response = FileResponse(
            pdf_io,
            content_type='application/pdf',
            as_attachment=True,
            filename=filename
        )
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    except Exception as e:
        logger.error(f"Erro ao retornar PDF: {e}")
        return HttpResponse("Erro ao processar arquivo", status=500)


@csrf_exempt
@require_http_methods(["GET"])
def verificar_token(request, token):
    """View auxiliar para verificar status de um token"""
    try:
        token_obj = get_object_or_404(ContratoDownloadToken, token=token)
        data = {
            'valido': not token_obj.esta_expirado,
            'expirado': token_obj.esta_expirado,
            'expira_em': token_obj.expira_em.isoformat(),
            'dias_restantes': token_obj.dias_restantes,
            'acessos': token_obj.acessos,
            'ultimo_acesso': token_obj.ultimo_acesso.isoformat() if token_obj.ultimo_acesso else None,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=404)
