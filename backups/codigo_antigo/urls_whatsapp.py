"""
URLs para Painel WhatsApp
Adicionar em core/urls.py
"""

from django.urls import path
from core.views_whatsapp import (
    painel_whatsapp,
    detalhe_comanda_whatsapp,
    api_mensagem_comanda  # Vamos criar esta view
)

# URLs a serem adicionadas
urlpatterns_whatsapp = [
    # Painel principal
    path('admin/whatsapp/', painel_whatsapp, name='painel_whatsapp'),
    
    # Detalhes de comanda específica
    path('admin/whatsapp/comanda/<uuid:comanda_id>/', 
         detalhe_comanda_whatsapp, 
         name='detalhe_comanda_whatsapp'),
    
    # API para buscar mensagem formatada (JSON)
    path('admin/whatsapp/comanda/<uuid:comanda_id>/mensagem/', 
         api_mensagem_comanda, 
         name='api_mensagem_comanda'),
]
