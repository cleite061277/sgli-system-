"""
Views auxiliares para download de contratos
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from .models import Locacao


@staff_member_required
def download_contrato_pdf(request, pk):
    from .admin import gerar_contrato_pdf
    locacao = get_object_or_404(Locacao, pk=pk)
    return gerar_contrato_pdf(locacao)


@staff_member_required
def download_contrato_docx(request, pk):
    from .admin import gerar_contrato_docx
    locacao = get_object_or_404(Locacao, pk=pk)
    return gerar_contrato_docx(locacao)
