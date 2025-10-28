"""
Middleware para capturar e logar erros em produção
"""
import logging
from django.http import JsonResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)

class ProductionErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Captura exceções e retorna página de erro amigável
        """
        logger.error(f"Erro capturado: {exception}", exc_info=True)
        
        # Se for requisição AJAX, retorna JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Erro interno do servidor',
                'message': str(exception)
            }, status=500)
        
        # Para requisições normais, renderiza página de erro
        return render(request, 'admin/error_500.html', {
            'error': str(exception),
            'user': request.user
        }, status=500)
