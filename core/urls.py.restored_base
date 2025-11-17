from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("""
    <html>
        <head><title>SGLI - Sistema Funcionando</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>🏢 SGLI - Sistema de Gestão de Locação de Imóveis</h1>
            <h2 style="color: green;">✅ Sistema Funcionando com API REST!</h2>
            <div style="margin: 30px;">
                <h3>📋 Acessos Disponíveis:</h3>
                <p><a href="/admin/" style="font-size: 18px;">🔐 Painel Administrativo</a></p>
                <p><a href="/api/" style="font-size: 18px;">🔗 API REST</a></p>
            </div>
            <div style="margin: 30px;">
                <h3>🏗️ Modelos Implementados:</h3>
                <ul style="list-style: none; font-size: 16px;">
                    <li>👥 Usuários (5 tipos: Admin, Gerente, Atendente, Financeiro, Locador)</li>
                    <li>🏠 Locadores (Proprietários)</li>
                    <li>🏢 Imóveis (Propriedades)</li>
                    <li>👤 Locatários (Inquilinos)</li>
                    <li>📄 Locações (Contratos)</li>
                </ul>
            </div>
            <p style="color: #666; margin-top: 40px;">
                <small>Versão: 1.0 | Debian/Policorp | Django 4.2.8</small>
            </p>
        </body>
    </html>
    """)

urlpatterns = [
    
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "SGLI - Administração"
admin.site.site_title = "SGLI Admin"
admin.site.index_title = "Sistema de Gestão de Locação de Imóveis"
