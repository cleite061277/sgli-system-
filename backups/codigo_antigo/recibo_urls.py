"""
Adicione estas URLs ao seu core/urls.py (ou sgli_project/urls.py)
"""

from django.urls import path
from core import views

urlpatterns = [
    # ... suas URLs existentes ...
    
    # URLs para recibo
    path('admin/visualizar-recibo/<int:pagamento_id>/', 
         views.visualizar_recibo_pagamento, 
         name='admin:visualizar_recibo_pagamento'),
    
    path('admin/download-recibo/<int:pagamento_id>/', 
         views.download_recibo_pdf, 
         name='admin:download_recibo_pdf'),
]
