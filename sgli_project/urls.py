"""
URL configuration - CORRIGIDO
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

# Views
#from core.views_whatsapp import painel_whatsapp, gerar_mensagem_whatsapp
##from core.views_comanda_web import comanda_web_view
from core.views_gerar_contrato import gerar_contrato_docx, gerar_contrato_pdf
from core.views import download_recibo_pagamento, pagina_recibo_pagamento
from core.dashboard_views import admin_index


def home_view(request):
    """Home page"""
    return HttpResponse('''
    <html>
        <head>
            <title>HABITAT PRO</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                h1 { font-size: 48px; margin: 20px 0; }
                a {
                    display: inline-block;
                    margin: 10px;
                    padding: 15px 30px;
                    background: white;
                    color: #667eea;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                }
                a:hover { transform: scale(1.05); }
            </style>
        </head>
        <body>
            <h1>🏢 HABITAT PRO</h1>
            <h2 style="color: #90EE90;">✅ Sistema Operacional</h2>
            <p><a href="/admin/">🔐 Acessar Dashboard</a></p>
        </body>
    </html>
    ''')


# === CUSTOMIZAÇÃO DO ADMIN (ANTES das URLs!) ===
admin.site.site_header = "HABITAT PRO - Administração"
admin.site.site_title = "HABITAT PRO Admin"
admin.site.index_title = "Sistema de Gestão Inteligente de Imóveis"
admin.site.index = admin_index


# === URL PATTERNS (TODAS JUNTAS!) ===
urlpatterns = [
    # Home
    path('', home_view, name='home'),
    
    # === WHATSAPP ===
#    path('admin/whatsapp/', painel_whatsapp, name='painel_whatsapp'),
#    path('admin/whatsapp/api/mensagem/<uuid:comanda_id>/', 
         #         gerar_mensagem_whatsapp, 
#         name='api_mensagem_comanda'),
    
    # === COMANDA WEB ===
#    path('comanda/<uuid:comanda_id>/<str:token>/', 
###         comanda_web_view, 
#         name='comanda_web'),
    
    # === CONTRATOS ===
    path('contrato/<uuid:locacao_id>/docx/', 
         gerar_contrato_docx, 
         name='gerar_contrato_docx'),
    path('contrato/<uuid:locacao_id>/pdf/', 
         gerar_contrato_pdf, 
         name='gerar_contrato_pdf'),
    
    # === RECIBOS ===
    path('pagamento/<uuid:pagamento_id>/recibo/', 
         pagina_recibo_pagamento, 
         name='pagina_recibo_pagamento'),
    path('pagamento/<uuid:pagamento_id>/recibo/download/', 
         download_recibo_pagamento, 
         name='download_recibo_pagamento'),
    
    # === PASSWORD RESET (CRÍTICO!) ===
    path('reset-senha/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
         ), 
         name='password_reset'),
    
    path('reset-senha/enviado/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('reset-senha/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    
    path('reset-senha/concluido/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # === ADMIN (UMA VEZ, NO FINAL) ===
    # LEGADO - Desativado DEV_20:     path('dashboard/', include('core.dashboard.urls')),
    # Vistorias (rotas públicas com token)
    path('', include('core.urls_inspection')),
    
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

# Servir media files em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Static/Media
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
