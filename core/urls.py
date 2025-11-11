"""
URLs do core - VERSÃO LIMPA
"""
from django.urls import path
from django.contrib import admin

from .views import (
    download_recibo_pagamento,
    pagina_recibo_pagamento,
)

from .views_whatsapp import (
    painel_whatsapp,
    gerar_mensagem_whatsapp,
)

urlpatterns = [
    # Painel WhatsApp
    path('admin/whatsapp/', 
         admin.site.admin_view(painel_whatsapp), 
         name='painel_whatsapp'),
    
    path('admin/whatsapp/gerar-mensagem/<uuid:comanda_id>/', 
         admin.site.admin_view(gerar_mensagem_whatsapp), 
         name='gerar_mensagem_whatsapp'),
    
    # Recibos
    path('pagamento/<uuid:pagamento_id>/recibo/', 
         pagina_recibo_pagamento, 
         name='pagina_recibo_pagamento'),
    
    path('pagamento/<uuid:pagamento_id>/recibo/download/', 
         download_recibo_pagamento, 
         name='download_recibo_pagamento'),
]
