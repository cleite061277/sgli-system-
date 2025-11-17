from django.http import HttpResponse
from django.template.loader import get_template
from django.shortcuts import get_object_or_404
from weasyprint import HTML
from io import BytesIO
from .models import Locacao, Comanda, Pagamento

def gerar_contrato_pdf(request, locacao_id):
    """Gerar contrato em PDF."""
    locacao = get_object_or_404(Locacao, id=locacao_id)
    
    template = get_template('documentos/contrato_locacao.html')
    html_content = template.render({'locacao': locacao})
    
    # Gerar PDF
    pdf_file = BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    pdf_file.seek(0)
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contrato_{locacao.numero_contrato}.pdf"'
    
    return response

def gerar_recibo_pagamento(request, pagamento_id):
    """Gerar recibo de pagamento."""
    pagamento = get_object_or_404(Pagamento, id=pagamento_id)
    
    template = get_template('documentos/recibo_pagamento.html')
    html_content = template.render({'pagamento': pagamento})
    
    pdf_file = BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    pdf_file.seek(0)
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recibo_{pagamento.id}.pdf"'
    
    return response
