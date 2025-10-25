from django.urls import path
from .views_gerar_contrato import gerar_contrato_docx, gerar_contrato_pdf

urlpatterns = [
    path('contrato/<uuid:locacao_id>/docx/', gerar_contrato_docx, name='gerar_contrato_docx'),
    path('contrato/<uuid:locacao_id>/pdf/', gerar_contrato_pdf, name='gerar_contrato_pdf'),
]
