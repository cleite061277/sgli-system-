from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet)
router.register(r'locadores', views.LocadorViewSet)
router.register(r'imoveis', views.ImovelViewSet)
router.register(r'locatarios', views.LocatarioViewSet)
router.register(r'locacoes', views.LocacaoViewSet)
router.register(r'comandas', views.ComandaViewSet)
router.register(r'relatorios', RelatoriosViewSet, basename='relatorios')

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('financeiro/', views.financeiro_view, name='financeiro'),
    path('api/', include(router.urls)),
]
