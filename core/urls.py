from django.urls import path
from django.contrib import admin

# ══════════════════════════════════════════════════════════════
# IMPORTS — Baseados na localização REAL das views
# ══════════════════════════════════════════════════════════════

# Views principais (core/views.py)
from .views import (
    enviar_comanda_email,
    pagina_recibo_pagamento,
    download_recibo_pagamento,
    recibo_publico,
    recibo_publico_pdf,
)

# Views de rescisão (core/views_rescisao.py)
from .views_rescisao import (
    confirmar_rescisao_view,
    comanda_rescisao_view,
)

# Views de download de contrato (core/views_download_contrato.py)
from .views_download_contrato import (
    download_contrato_token,
    verificar_token,
)

# Views de dashboard financeiro (core/dashboard_views.py)
from .dashboard_views import (
    dashboard_financeiro,
    exportar_dashboard_excel,
    exportar_dashboard_pdf,
    enviar_relatorio_email,
)

# Views de renovação (core/views_renovacao.py)
from . import views_renovacao

# Views de comanda web (core/views_comanda_web.py)
from .views_comanda_web import comanda_web_view



# ══════════════════════════════════════════════════════════════
# URLPATTERNS — Rotas do sistema
# ══════════════════════════════════════════════════════════════

urlpatterns = [    
    path('comanda/<uuid:comanda_id>/enviar-email/', enviar_comanda_email, name='enviar_comanda_email'),
    path('comanda/<uuid:comanda_id>/<str:token>/', comanda_web_view, name='comanda_web_view'),
    
    # URLs Públicas - Rescisão de Contratos
    path('rescisao/confirmar/<uuid:token>/', confirmar_rescisao_view, name='confirmar_rescisao'),
    path('comanda-rescisao/<uuid:token_publico>/', comanda_rescisao_view, name='comanda_rescisao'),
    
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
    
    # ══════════════════════════════════════════════════════════════
    # RECIBO PÚBLICO — Links seguros via token UUID
    # ══════════════════════════════════════════════════════════════
    path('recibo/<uuid:token>/', recibo_publico, name='recibo_publico'),
    path('recibo/<uuid:token>/pdf/', recibo_publico_pdf, name='recibo_publico_pdf'),
]
