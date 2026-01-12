"""
URLs para Sistema de Vistorias (Inspection)
Rotas públicas acessíveis via token
Autor: Claude + Cícero (Policorp)
Data: 11/01/2026
"""
from django.urls import path
from core import views_inspection

urlpatterns = [
    # View mobile (GET) - abre formulário
    path(
        'vistoria/<str:token>/',
        views_inspection.abrir_vistoria_mobile,
        name='inspection_mobile_form'
    ),
    
    # Upload de foto (POST)
    path(
        'vistoria/<str:token>/upload/',
        views_inspection.upload_foto_vistoria,
        name='inspection_upload_foto'
    ),
    
    # Deletar foto (POST)
    path(
        'vistoria/<str:token>/foto/<uuid:foto_id>/deletar/',
        views_inspection.deletar_foto_vistoria,
        name='inspection_deletar_foto'
    ),
    
    # Finalizar vistoria e gerar PDF (POST)
    path(
        'vistoria/<str:token>/finalizar/',
        views_inspection.finalizar_vistoria,
        name='inspection_finalizar'
    ),
]
