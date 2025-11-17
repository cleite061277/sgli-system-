"""
URLs do core - Dashboards e funcionalidades principais
"""
from django.urls import path
from .views_gerar_contrato import gerar_contrato_docx, gerar_contrato_pdf
from .views import download_recibo_pagamento, pagina_recibo_pagamento
from .dashboard_views import admin_index, dashboard_financeiro

urlpatterns = [
    # === DASHBOARDS ===
    # Dashboard Principal (Index customizado)
    path('', admin_index, name='admin_custom_index'),
    
    # Dashboard Financeiro
    path('dashboard-financeiro/', dashboard_financeiro, name='dashboard_financeiro'),
    
    # === CONTRATOS ===
    path('contrato/<uuid:locacao_id>/docx/', gerar_contrato_docx, name='gerar_contrato_docx'),
    path('contrato/<uuid:locacao_id>/pdf/', gerar_contrato_pdf, name='gerar_contrato_pdf'),
    
    # === RECIBOS ===
    # Página de visualização e envio
    path('pagamento/<uuid:pagamento_id>/recibo/', 
         pagina_recibo_pagamento, 
         name='pagina_recibo_pagamento'),
    
    # Download do recibo
    path('pagamento/<uuid:pagamento_id>/recibo/download/', 
         download_recibo_pagamento, 
         name='download_recibo_pagamento'),
]
