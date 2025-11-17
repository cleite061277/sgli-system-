"""
Views customizadas para Admin Dashboard e Dashboard Financeiro
Recriado completamente - Versão Master
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from .models import Imovel, Locacao, Locatario, Pagamento, Comanda


# ===========================================================================
# FUNÇÃO 1: DASHBOARD INICIAL (Admin Index - Página Principal)
# ===========================================================================

@staff_member_required
def admin_index(request):
    """
    Dashboard inicial personalizado que substitui a página padrão do Django Admin.
    Exibe métricas principais e comandas vencidas.
    """
    hoje = timezone.now().date()
    
    # === MÉTRICAS PRINCIPAIS ===
    
    # Total de imóveis ativos
    total_imoveis = Imovel.objects.filter(is_active=True).count()
    
    # Contratos de locação ativos
    contratos_ativos = Locacao.objects.filter(
        status='ACTIVE',
        is_active=True
    ).count()
    
    # Total de locatários cadastrados
    total_locatarios = Locatario.objects.filter(is_active=True).count()
    
    # Contratos vencendo nos próximos 60 dias
    data_limite_60 = hoje + timedelta(days=60)
    contratos_vencendo = Locacao.objects.filter(
        data_fim__lte=data_limite_60,
        data_fim__gte=hoje,
        status='ACTIVE',
        is_active=True
    ).count()
    
    # Receita do mês atual
    inicio_mes = hoje.replace(day=1)
    receita_mes = Pagamento.objects.filter(
        data_pagamento__gte=inicio_mes,
        data_pagamento__lte=hoje,
        status='CONFIRMADO',
        is_active=True
    ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0')
    
    # Taxa de inadimplência
    total_comandas_vencidas = Comanda.objects.filter(
        data_vencimento__lt=hoje,
        is_active=True
    ).count()
    
    comandas_pendentes = Comanda.objects.filter(
        data_vencimento__lt=hoje,
        status__in=['PENDENTE', 'VENCIDA'],
        is_active=True
    ).count()
    
    taxa_inadimplencia = 0
    if total_comandas_vencidas > 0:
        taxa_inadimplencia = round(
            (comandas_pendentes / total_comandas_vencidas) * 100, 
            1
        )
    
    # === COMANDAS VENCIDAS (últimas 10) ===
    comandas_vencidas = Comanda.objects.filter(
        data_vencimento__lt=hoje,
        status__in=['PENDENTE', 'VENCIDA'],
        is_active=True
    ).select_related(
        'locacao__locatario',
        'locacao__imovel'
    ).order_by('data_vencimento')[:10]
    
    # Calcular dias de atraso para cada comanda
    for comanda in comandas_vencidas:
        comanda.dias_atraso = (hoje - comanda.data_vencimento).days
    
    # === CONTEXTO PARA O TEMPLATE ===
    context = {
        # Metadados do admin
        'title': 'Dashboard Principal - HABITAT PRO',
        'site_title': 'HABITAT PRO',
        'site_header': 'HABITAT PRO - Administração',
        'has_permission': True,
        
        # Métricas (cards superiores)
        'total_imoveis': total_imoveis,
        'contratos_ativos': contratos_ativos,
        'total_locatarios': total_locatarios,
        'contratos_vencendo': contratos_vencendo,
        'receita_mes': receita_mes,
        'taxa_inadimplencia': taxa_inadimplencia,
        
        # Dados das tabelas
        'comandas_vencidas': comandas_vencidas,
        
        # App list para a seção de modelos (mantém compatibilidade com Django)
        'app_list': [],  # Pode ser populado se necessário
    }
    
    return render(request, 'admin/index.html', context)


# ===========================================================================
# FUNÇÃO 2: DASHBOARD FINANCEIRO (Análise Completa)
# ===========================================================================

@staff_member_required
def dashboard_financeiro(request):
    """
    Dashboard financeiro completo com:
    - 4 Cards de métricas principais
    - Gráfico de linha (receita 12 meses)
    - Gráfico de pizza (formas de pagamento)
    - 3 Tabelas (pagamentos recentes, comandas vencidas, previsão)
    """
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    inicio_ano = hoje.replace(month=1, day=1)
    
    # === CARDS DE MÉTRICAS ===
    
    # 1. Receita do mês atual
    receita_mes = Pagamento.objects.filter(
        data_pagamento__gte=inicio_mes,
        data_pagamento__lte=hoje,
        status='CONFIRMADO',
        is_active=True
    ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0')
    
    # 2. Receita do ano
    receita_ano = Pagamento.objects.filter(
        data_pagamento__gte=inicio_ano,
        data_pagamento__lte=hoje,
        status='CONFIRMADO',
        is_active=True
    ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0')
    
    # 3. Contratos ativos
    contratos_ativos = Locacao.objects.filter(
        status='ACTIVE',
        is_active=True
    ).count()
    
    # 4. Taxa de inadimplência
    total_comandas = Comanda.objects.filter(
        data_vencimento__lt=hoje,
        is_active=True
    ).count()
    
    comandas_pendentes = Comanda.objects.filter(
        data_vencimento__lt=hoje,
        status__in=['PENDENTE', 'VENCIDA'],
        is_active=True
    ).count()
    
    taxa_inadimplencia = 0
    if total_comandas > 0:
        taxa_inadimplencia = round((comandas_pendentes / total_comandas) * 100, 1)
    
    # === GRÁFICO 1: RECEITA ÚLTIMOS 12 MESES ===
    inicio_12_meses = hoje - timedelta(days=365)
    receita_mensal = Pagamento.objects.filter(
        data_pagamento__gte=inicio_12_meses,
        status='CONFIRMADO',
        is_active=True
    ).annotate(
        mes=TruncMonth('data_pagamento')
    ).values('mes').annotate(
        total=Sum('valor_pago')
    ).order_by('mes')
    
    # Preparar dados para Chart.js (formato JSON)
    meses_labels = []
    meses_valores = []
    for item in receita_mensal:
        # Formatar mês: "Jan/2025"
        mes_formatado = item['mes'].strftime('%b/%Y')
        meses_labels.append(mes_formatado)
        meses_valores.append(float(item['total']))
    
    # === GRÁFICO 2: PAGAMENTOS POR FORMA ===
    pagamentos_forma = Pagamento.objects.filter(
        data_pagamento__gte=inicio_ano,
        status='CONFIRMADO',
        is_active=True
    ).values('forma_pagamento').annotate(
        total=Sum('valor_pago'),
        quantidade=Count('id')
    ).order_by('-total')
    
    formas_labels = []
    formas_valores = []
    for item in pagamentos_forma:
        # Converter código para nome legível
        forma_nome = dict(Pagamento.FORMA_PAGAMENTO_CHOICES).get(
            item['forma_pagamento'], 
            'Outro'
        )
        formas_labels.append(forma_nome)
        formas_valores.append(float(item['total']))
    
    # === TABELA 1: PAGAMENTOS RECENTES ===
    pagamentos_recentes = Pagamento.objects.filter(
        is_active=True
    ).select_related(
        'comanda__locacao__locatario',
        'comanda__locacao__imovel'
    ).order_by('-data_pagamento')[:10]
    
    # === TABELA 2: COMANDAS VENCIDAS ===
    comandas_vencidas = Comanda.objects.filter(
        data_vencimento__lt=hoje,
        status__in=['PENDENTE', 'VENCIDA'],
        is_active=True
    ).select_related(
        'locacao__locatario',
        'locacao__imovel'
    ).order_by('data_vencimento')[:10]
    
    # Adicionar dias de atraso
    for cmd in comandas_vencidas:
        cmd.dias_atraso = (hoje - cmd.data_vencimento).days
    
    # === TABELA 3: PREVISÃO DE RECEBIMENTOS (próximos 30 dias) ===
    fim_periodo = hoje + timedelta(days=30)
    previsao_recebimentos = Comanda.objects.filter(
        data_vencimento__gte=hoje,
        data_vencimento__lte=fim_periodo,
        status='PENDENTE',
        is_active=True
    ).select_related(
        'locacao__locatario',
        'locacao__imovel'
    ).order_by('data_vencimento')
    
    # Total previsto
    previsao_total = previsao_recebimentos.aggregate(
        total=Sum('valor_total')
    )['total'] or Decimal('0')
    
    # === CONTEXTO PARA O TEMPLATE ===
    context = {
        # Metadados
        'title': 'Dashboard Financeiro - HABITAT PRO',
        'site_title': 'HABITAT PRO',
        'site_header': 'HABITAT PRO - Administração',
        'has_permission': True,
        
        # Cards de métricas
        'receita_mes': receita_mes,
        'receita_ano': receita_ano,
        'contratos_ativos': contratos_ativos,
        'taxa_inadimplencia': taxa_inadimplencia,
        
        # Dados dos gráficos (em formato JSON para Chart.js)
        'meses_labels': meses_labels,
        'meses_valores': meses_valores,
        'formas_labels': formas_labels,
        'formas_valores': formas_valores,
        
        # Dados das tabelas
        'pagamentos_recentes': pagamentos_recentes,
        'comandas_vencidas': comandas_vencidas,
        'previsao_recebimentos': previsao_recebimentos,
        'previsao_total': previsao_total,
    }
    
    return render(request, 'admin/dashboard_financeiro.html', context)
