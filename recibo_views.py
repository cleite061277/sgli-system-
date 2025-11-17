"""
Adicione estas views ao seu core/views.py
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Pagamento
from django.template.loader import render_to_string

@staff_member_required
def visualizar_recibo_pagamento(request, pagamento_id):
    """Exibe recibo em modal HTML bonito"""
    pagamento = get_object_or_404(Pagamento, pk=pagamento_id)
    
    context = {
        'pagamento': pagamento,
        'comanda': pagamento.comanda,
        'locacao': pagamento.comanda.locacao,
        'locatario': pagamento.comanda.locacao.locatario,
        'imovel': pagamento.comanda.locacao.imovel,
    }
    
    return render(request, 'admin/recibo_modal.html', context)


@staff_member_required
def download_recibo_pdf(request, pagamento_id):
    """Gera PDF do recibo"""
    from .document_generator import DocumentGenerator
    
    pagamento = get_object_or_404(Pagamento, pk=pagamento_id)
    generator = DocumentGenerator()
    
    try:
        filename = generator.gerar_recibo_pagamento(pagamento_id)
        # Retornar arquivo para download
        # ... implementação de download
        return HttpResponse("PDF gerado com sucesso!")
    except Exception as e:
        return HttpResponse(f"Erro: {e}", status=500)
