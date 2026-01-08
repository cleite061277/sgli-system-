from core.views_download_contrato import download_contrato_token, verificar_token
"""
URLs do core - VERSÃO DEV_21
Adicionado: Rotas de Renovação de Contratos
"""
from django.urls import path
from django.contrib import admin

from .views import (
    comanda_web_view,
    enviar_comanda_email,
    download_recibo_pagamento,
    pagina_recibo_pagamento,
)

# ✅ DEV_20: Import das views do dashboard
from .dashboard_views import (
    dashboard_financeiro,
    exportar_dashboard_excel,
    exportar_dashboard_pdf,
    enviar_relatorio_email
)

# ✅ DEV_21: Import das views de renovação
from . import views_renovacao

urlpatterns = [    
    path('comanda/<uuid:comanda_id>/<str:token>/', comanda_web_view, name='comanda_web_view'),
    path('comanda/<uuid:comanda_id>/enviar-email/', enviar_comanda_email, name='enviar_comanda_email'),
    
    # Recibos
    path('pagamento/<uuid:pagamento_id>/recibo/', 
         pagina_recibo_pagamento, 
         name='pagina_recibo_pagamento'),
    
    path('pagamento/<uuid:pagamento_id>/recibo/download/', 
         download_recibo_pagamento, 
         name='download_recibo_pagamento'),
    
    # ✅ DEV_20: Dashboard Financeiro
    path('dashboard/financeiro/', 
         admin.site.admin_view(dashboard_financeiro), 
         name='dashboard_financeiro'),
    
    path('dashboard/financeiro/excel/', 
         admin.site.admin_view(exportar_dashboard_excel), 
         name='exportar_dashboard_excel'),
    
    path('dashboard/financeiro/pdf/', 
         admin.site.admin_view(exportar_dashboard_pdf), 
         name='exportar_dashboard_pdf'),
    
    path('dashboard/financeiro/email/', 
         admin.site.admin_view(enviar_relatorio_email), 
         name='enviar_relatorio_email'),
    
    # ✅ DEV_21: Rotas Públicas de Renovação (sem autenticação)
    path('renovacao/proprietario/<uuid:token>/', 
         views_renovacao.responder_renovacao_proprietario, 
         name='responder_renovacao_proprietario'),
    
    path('renovacao/locatario/<uuid:token>/', 
         views_renovacao.responder_renovacao_locatario, 
         name='responder_renovacao_locatario'),
    # URLs de download de contrato via token
    path('contrato/<uuid:token>/', download_contrato_token, name='download_contrato_token'),
    path('contrato/<uuid:token>/status/', verificar_token, name='verificar_token_contrato'),

]
