"""
View customizada para Dashboard do Admin
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Q
from datetime import datetime, timedelta
from .models import Imovel, Locacao, Locatario


@staff_member_required
def admin_dashboard(request):
    """Dashboard customizada com estatísticas."""
    
    # Calcular estatísticas
    total_imoveis = Imovel.objects.filter(is_active=True).count()
    
    contratos_ativos = Locacao.objects.filter(
        status='ATIVA',
        is_active=True
    ).count()
    
    total_locatarios = Locatario.objects.filter(is_active=True).count()
    
    # Contratos vencendo nos próximos 60 dias
    data_limite = datetime.now().date() + timedelta(days=60)
    contratos_vencendo = Locacao.objects.filter(
        status='ATIVA',
        data_fim__lte=data_limite,
        is_active=True
    ).count()
    
    context = {
        'total_imoveis': total_imoveis,
        'contratos_ativos': contratos_ativos,
        'total_locatarios': total_locatarios,
        'contratos_vencendo': contratos_vencendo,
        'title': 'Dashboard',
        'site_title': 'HABITAT PRO',
        'site_header': 'HABITAT PRO - Administração',
    }
    
    return render(request, 'admin/index.html', context)
