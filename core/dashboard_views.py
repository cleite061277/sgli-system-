"""
Views customizadas para Admin Dashboard
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from datetime import datetime, timedelta
from .models import Imovel, Locacao, Locatario


@staff_member_required
def admin_index(request):
    """Dashboard customizada com estatísticas."""
    hoje = datetime.now().date()
    data_limite = hoje + timedelta(days=60)
    
    total_imoveis = Imovel.objects.filter(is_active=True).count()
    # ✅ CORREÇÃO: status='ACTIVE' (valor do DB) ao invés de 'ATIVA' (label)
    contratos_ativos = Locacao.objects.filter(status='ACTIVE', is_active=True).count()
    total_locatarios = Locatario.objects.filter(is_active=True).count()
    contratos_vencendo = Locacao.objects.filter(
        status='ACTIVE',  # ✅ CORRIGIDO
        data_fim__gte=hoje,
        data_fim__lte=data_limite,
        is_active=True
    ).count()
    
    context = {
        'total_imoveis': total_imoveis,
        'contratos_ativos': contratos_ativos,
        'total_locatarios': total_locatarios,
        'contratos_vencendo': contratos_vencendo,
        'title': 'Dashboard - HABITAT PRO',
        'site_title': 'HABITAT PRO',
        'site_header': 'HABITAT PRO',
        'has_permission': True,
    }
    
    return render(request, 'admin/index.html', context)
