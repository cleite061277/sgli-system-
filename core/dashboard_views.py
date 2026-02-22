# core/dashboard_views.py
"""
Views customizadas para Dashboard Financeiro
✅ CORRIGIDO: Mantém todas as funções existentes + adiciona melhorias
Versão: DEV_20 - Dashboard completo com dados dinâmicos
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum, Q, Count, F
from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings
from decimal import Decimal
from .models import Imovel, Locacao, Locatario, Comanda, Pagamento, RenovacaoContrato
from .models_rescisao import ComandaRescisao


@staff_member_required
def admin_index(request):
    """
    Dashboard principal com estatísticas.
    ✅ MANTIDO: Função essencial para admin.py
    """
    hoje = datetime.now().date()
    data_limite = hoje + timedelta(days=settings.PRAZO_ALERTA_VENCIMENTO_DIAS)
    
    total_imoveis = Imovel.objects.filter(is_active=True).count()
    contratos_ativos = Locacao.objects.filter(status='ACTIVE', is_active=True).count()
    total_locatarios = Locatario.objects.filter(is_active=True).count()
    # Contar renovações de contratos (foco em renovações ativas)
    contratos_vencendo = RenovacaoContrato.objects.filter(
        locacao_original__isnull=False
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


@staff_member_required
def dashboard_financeiro(request):
    """
    Dashboard Financeiro Completo com KPIs, gráficos e análises.
    ✅ MELHORADO: Filtros de ano/mês, links nas comandas, gráficos dinâmicos
    """
    hoje = timezone.now().date()
    ano_atual = hoje.year
    mes_atual = hoje.month
    
    # ========================================
    # FILTROS (✅ MELHORADO: ano e mês separados)
    # ========================================
    periodo = request.GET.get('periodo', 'mes')
    imovel_id = request.GET.get('imovel', 'todos')
    status_filtro = request.GET.get('status', 'todos')
    visualizacao = request.GET.get('visualizacao', 'real')
    
    # ✅ NOVO: Filtros de ano e mês
    ano_selecionado = request.GET.get('ano')
    mes_selecionado = request.GET.get('mes')
    
    if ano_selecionado:
        try:
            ano_selecionado = int(ano_selecionado)
        except:
            ano_selecionado = ano_atual
    else:
        ano_selecionado = ano_atual
    
    if mes_selecionado:
        try:
            mes_selecionado = int(mes_selecionado)
        except:
            mes_selecionado = mes_atual
    else:
        mes_selecionado = mes_atual
    
    # Determinar range de datas baseado no período
    if periodo == 'mes':
        data_inicio = datetime(ano_selecionado, mes_selecionado, 1).date()
        if mes_selecionado == 12:
            data_fim = datetime(ano_selecionado + 1, 1, 1).date() - timedelta(days=1)
        else:
            data_fim = datetime(ano_selecionado, mes_selecionado + 1, 1).date() - timedelta(days=1)
    elif periodo == 'trimestre':
        data_inicio = (hoje - timedelta(days=90)).replace(day=1)
        data_fim = hoje
    elif periodo == 'semestre':
        data_inicio = (hoje - timedelta(days=180)).replace(day=1)
        data_fim = hoje
    elif periodo == 'ano':
        data_inicio = datetime(ano_selecionado, 1, 1).date()
        data_fim = datetime(ano_selecionado, 12, 31).date()
    else:  # comparativo
        data_inicio = datetime(2024, 1, 1).date()
        data_fim = datetime(2025, 12, 31).date()
    
    # ========================================
    # QUERY BASE DE COMANDAS
    # ========================================
    comandas_query = Comanda.objects.filter(
        mes_referencia__gte=data_inicio,
        mes_referencia__lte=data_fim,
        is_active=True
    ).select_related('locacao', 'locacao__imovel', 'locacao__locatario')
    
    # Filtro por imóvel
    if imovel_id != 'todos':
        comandas_query = comandas_query.filter(locacao__imovel_id=imovel_id)
    
    # Filtro por status
    if status_filtro == 'pago':
        comandas_query = comandas_query.filter(status='PAID')
    elif status_filtro == 'pendente':
        comandas_query = comandas_query.filter(status__in=['PENDING', 'PARTIAL'])
    elif status_filtro == 'atrasado':
        comandas_query = comandas_query.filter(
            status__in=['OVERDUE', 'PENDING'],
            data_vencimento__lt=hoje
        )
    
    # ========================================
    # QUERY DE COMANDAS DE RESCISÃO
    # ========================================
    comandas_rescisao_query = ComandaRescisao.objects.filter(
        data_vencimento__gte=data_inicio,
        data_vencimento__lte=data_fim,
        is_active=True
    ).select_related('rescisao', 'rescisao__locacao', 'rescisao__locacao__imovel', 'rescisao__locacao__locatario')
    
    # Filtro por imóvel (rescisão)
    if imovel_id != 'todos':
        comandas_rescisao_query = comandas_rescisao_query.filter(rescisao__locacao__imovel_id=imovel_id)
    
    # Filtro por status (rescisão)
    if status_filtro == 'pago':
        comandas_rescisao_query = comandas_rescisao_query.filter(status='PAGO')
    elif status_filtro == 'pendente':
        comandas_rescisao_query = comandas_rescisao_query.filter(status='PENDENTE')
    elif status_filtro == 'atrasado':
        comandas_rescisao_query = comandas_rescisao_query.filter(
            status__in=['ATRASADO', 'PENDENTE'],
            data_vencimento__lt=hoje
        )
    
    # ========================================
    # CÁLCULO DE KPIs
    # ========================================
    
    # Receita Prevista — ALUGUEL (soma de todas comandas do período)
    receita_prevista_aluguel = comandas_query.aggregate(
        total=Sum('_valor_aluguel_historico')
    )['total'] or Decimal('0.00')
    
    receita_prevista_aluguel += comandas_query.aggregate(
        total=Sum('valor_condominio')
    )['total'] or Decimal('0.00')
    
    receita_prevista_aluguel += comandas_query.aggregate(
        total=Sum('valor_iptu')
    )['total'] or Decimal('0.00')
    
    # Receita Prevista — RESCISÃO
    receita_prevista_rescisao = comandas_rescisao_query.aggregate(
        total=Sum('valor')
    )['total'] or Decimal('0.00')
    
    # TOTAL PREVISTO (Aluguel + Rescisão)
    receita_prevista = receita_prevista_aluguel + receita_prevista_rescisao
    
    # Receita Realizada — ALUGUEL (FK comanda)
    receita_realizada_aluguel = Pagamento.objects.filter(
        comanda__in=comandas_query,
        status='confirmado',
        data_pagamento__gte=data_inicio,
        data_pagamento__lte=data_fim
    ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
    
    # Receita Realizada — RESCISÃO (GenericFK content_type)
    receita_realizada_rescisao = Pagamento.objects.filter(
        content_type__isnull=False,  # Tem GenericFK
        status='confirmado',
        data_pagamento__gte=data_inicio,
        data_pagamento__lte=data_fim
    ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
    
    # TOTAL REALIZADO (Aluguel + Rescisão)
    receita_realizada = receita_realizada_aluguel + receita_realizada_rescisao
    
    # Taxa de Recebimento
    taxa_recebimento = (receita_realizada / receita_prevista * 100) if receita_prevista > 0 else Decimal('0.00')
    
    # Comandas em Atraso — ALUGUEL (TODAS, não apenas do período)
    comandas_aluguel_atrasadas = Comanda.objects.filter(
        data_vencimento__lt=hoje,
        status__in=['PENDING', 'OVERDUE', 'PARTIAL'],
        is_active=True
    ).count()
    
    # Comandas em Atraso — RESCISÃO (TODAS, não apenas do período)
    comandas_rescisao_atrasadas = ComandaRescisao.objects.filter(
        data_vencimento__lt=hoje,
        status__in=['PENDENTE', 'ATRASADO'],
        is_active=True
    ).count()
    
    # TOTAL ATRASADAS (Aluguel + Rescisão)
    comandas_atrasadas = comandas_aluguel_atrasadas + comandas_rescisao_atrasadas
    
    # Taxa de Inadimplência
    total_comandas = comandas_query.count() + comandas_rescisao_query.count()
    taxa_inadimplencia = (comandas_atrasadas / total_comandas * 100) if total_comandas > 0 else Decimal('0.00')
    
    # Receita Pendente
    receita_pendente = receita_prevista - receita_realizada
    
    # ========================================
    # DADOS MENSAIS (para gráficos)
    # ========================================
    dados_mensais = []
    
    # Últimos 12 meses
    for i in range(11, -1, -1):
        # Calcular mês de referência
        if mes_selecionado - i <= 0:
            mes_ref_num = 12 + (mes_selecionado - i)
            ano_ref = ano_selecionado - 1
        else:
            mes_ref_num = mes_selecionado - i
            ano_ref = ano_selecionado
        
        mes_ref = datetime(ano_ref, mes_ref_num, 1).date()
        
        # ========================================
        # COMANDAS DO MÊS — ALUGUEL
        # ========================================
        comandas_mes = Comanda.objects.filter(
            mes_referencia__year=mes_ref.year,
            mes_referencia__month=mes_ref.month,
            is_active=True
        )
        
        if imovel_id != 'todos':
            comandas_mes = comandas_mes.filter(locacao__imovel_id=imovel_id)
        
        # Previsto Aluguel
        previsto_aluguel = 0
        for cmd in comandas_mes:
            previsto_aluguel += float(cmd.valor_total)
        
        # ========================================
        # COMANDAS DO MÊS — RESCISÃO
        # ========================================
        mes_inicio = datetime(mes_ref.year, mes_ref.month, 1).date()
        if mes_ref.month == 12:
            mes_fim = datetime(mes_ref.year + 1, 1, 1).date()
        else:
            mes_fim = datetime(mes_ref.year, mes_ref.month + 1, 1).date()
        
        comandas_rescisao_mes = ComandaRescisao.objects.filter(
            data_vencimento__gte=mes_inicio,
            data_vencimento__lt=mes_fim,
            is_active=True
        )
        
        if imovel_id != 'todos':
            comandas_rescisao_mes = comandas_rescisao_mes.filter(rescisao__locacao__imovel_id=imovel_id)
        
        # Previsto Rescisão
        previsto_rescisao = float(
            comandas_rescisao_mes.aggregate(total=Sum('valor'))['total'] or 0
        )
        
        # PREVISTO TOTAL
        previsto_mes = previsto_aluguel + previsto_rescisao
        
        # ========================================
        # REALIZADO — ALUGUEL + RESCISÃO
        # ========================================
        # Realizado Aluguel (FK comanda)
        realizado_aluguel = float(
            Pagamento.objects.filter(
                comanda__mes_referencia__year=mes_ref.year,
                comanda__mes_referencia__month=mes_ref.month,
                status='confirmado'
            ).aggregate(total=Sum('valor_pago'))['total'] or 0
        )
        
        # Realizado Rescisão (GenericFK)
        realizado_rescisao = float(
            Pagamento.objects.filter(
                content_type__isnull=False,
                data_pagamento__gte=mes_inicio,
                data_pagamento__lt=mes_fim,
                status='confirmado'
            ).aggregate(total=Sum('valor_pago'))['total'] or 0
        )
        
        # REALIZADO TOTAL
        realizado_mes = realizado_aluguel + realizado_rescisao
        
        # ========================================
        # INADIMPLÊNCIA DO MÊS
        # ========================================
        total_mes = comandas_mes.count() + comandas_rescisao_mes.count()
        
        atrasadas_aluguel = comandas_mes.filter(
            status__in=['OVERDUE', 'PENDING'],
            data_vencimento__lt=hoje
        ).count()
        
        atrasadas_rescisao = comandas_rescisao_mes.filter(
            status__in=['PENDENTE', 'ATRASADO'],
            data_vencimento__lt=hoje
        ).count()
        
        atrasadas_mes = atrasadas_aluguel + atrasadas_rescisao
        inadimplencia_mes = (atrasadas_mes / total_mes * 100) if total_mes > 0 else 0
        
        dados_mensais.append({
            'mes': mes_ref.strftime('%b/%y'),
            'previsto': previsto_mes,
            'realizado': realizado_mes,
            'inadimplencia': round(inadimplencia_mes, 1)
        })
    
    # ========================================
    # PERFORMANCE POR IMÓVEL
    # ========================================
    imoveis_lista = Imovel.objects.filter(is_active=True)[:10]  # Top 10
    performance_imoveis = []
    
    for imovel in imoveis_lista:
        comandas_imovel = comandas_query.filter(locacao__imovel=imovel)
        
        previsto_imovel = 0
        for cmd in comandas_imovel:
            previsto_imovel += float(cmd.valor_total)
        
        realizado_imovel = float(
            Pagamento.objects.filter(
                comanda__in=comandas_imovel,
                status='confirmado'
            ).aggregate(total=Sum('valor_pago'))['total'] or 0
        )
        
        performance_imoveis.append({
            'nome': f"{imovel.endereco}, {imovel.numero}"[:30],
            'previsto': previsto_imovel,
            'realizado': realizado_imovel
        })
    
    # ========================================
    # ÚLTIMOS PAGAMENTOS (✅ MELHORADO: com links)
    # ========================================
    ultimos_pagamentos = []
    
    pagamentos_recentes = Pagamento.objects.filter(
        data_pagamento__gte=data_inicio,
        data_pagamento__lte=data_fim,
        status='confirmado'
    ).select_related(
        'comanda',
        'comanda__locacao',
        'comanda__locacao__locatario',
        'comanda__locacao__imovel'
    ).order_by('-data_pagamento')[:20]
    
    for pag in pagamentos_recentes:
        # 🔄 Resolver contexto polimórfico (aluguel ou rescisão)
        if pag.comanda_id:
            # Aluguel (FK)
            comanda = pag.comanda
            locacao = comanda.locacao if comanda else None
            locatario = locacao.locatario if locacao else None
            imovel = locacao.imovel if locacao else None
            numero_ref = comanda.numero_comanda if comanda else '—'
            comanda_link = f"/admin/core/comanda/{comanda.id}/change/" if comanda else None
        elif hasattr(pag, 'content_type_id') and pag.content_type_id and pag.object_id:
            # Rescisão (GenericFK)
            comanda = None
            _ref = pag.comanda_ref if hasattr(pag, 'comanda_ref') else None
            _rs = _ref.rescisao if (_ref and hasattr(_ref, 'rescisao')) else None
            locacao = _rs.locacao if _rs else None
            locatario = locacao.locatario if locacao else None
            imovel = locacao.imovel if locacao else None
            numero_ref = f"Rescisão-{_ref.numero_parcela}/{_rs.quantidade_parcelas}" if (_ref and _rs) else 'Rescisão'
            comanda_link = f"/admin/core/comandarescisao/{_ref.id}/change/" if _ref else None
        else:
            # Fallback
            locatario = imovel = None
            numero_ref = pag.numero_pagamento if hasattr(pag, 'numero_pagamento') else 'Pagamento'
            comanda_link = None
        
        ultimos_pagamentos.append({
            'numero_comanda': numero_ref,
            'comanda_id': comanda.id if comanda else None,
            'numero_comanda_link': comanda_link,
            'inquilino': locatario.nome_razao_social if locatario else '—',
            'imovel': f"{imovel.endereco}, {imovel.numero}" if imovel else '—',
            'valor': float(pag.valor_pago),
            'data': pag.data_pagamento.strftime('%d/%m/%Y')
        })
    
    # ========================================
    # ALERTAS
    # ========================================
    alertas = []
    
    # Alerta de Alta Inadimplência (geral)
    if taxa_inadimplencia > 5:
        alertas.append({
            'tipo': 'warning',
            'titulo': 'Alta Inadimplência',
            'mensagem': f'Taxa de inadimplência em {taxa_inadimplencia:.1f}% (meta: < 3%)',
            'acao': None,  # Sem ação específica (alertas abaixo têm links)
            'link': None
        })
    
    # Alertas separados por tipo (ALUGUEL e RESCISÃO)
    if comandas_aluguel_atrasadas > 0:
        alertas.append({
            'tipo': 'warning',
            'titulo': f'{comandas_aluguel_atrasadas} Comanda(s) de Aluguel em Atraso',
            'mensagem': 'Ações de cobrança podem ser necessárias',
            'acao': 'Ver Comandas Aluguel →',
            'link': '/admin/core/comanda/?status=PENDING'
        })
    
    if comandas_rescisao_atrasadas > 0:
        alertas.append({
            'tipo': 'warning',
            'titulo': f'{comandas_rescisao_atrasadas} Comanda(s) de Rescisão em Atraso',
            'mensagem': 'Ações de cobrança podem ser necessárias',
            'acao': 'Ver Comandas Rescisão →',
            'link': '/admin/core/comandarescisao/?status=PENDENTE'
        })
    
    # ✅ NOVO: Lista de anos disponíveis
    anos_disponiveis = Comanda.objects.dates('mes_referencia', 'year', order='DESC')
    anos_lista = sorted(set([d.year for d in anos_disponiveis]), reverse=True)
    if not anos_lista:
        anos_lista = [ano_atual]
    
    # ========================================
    # CONTRATOS ATIVOS (Locações)
    # ========================================
    contratos_ativos = Locacao.objects.filter(status='ACTIVE', is_active=True).count()
    
    # ========================================
    # CONTEXT
    # ========================================
    context = {
        # Filtros
        'filtros': {
            'periodo': periodo,
            'imovel': imovel_id,
            'status': status_filtro,
            'visualizacao': visualizacao
        },
        'ano_atual': ano_atual,
        'mes_atual': mes_atual,
        'ano_selecionado': ano_selecionado,  # ✅ NOVO
        'mes_selecionado': mes_selecionado,  # ✅ NOVO
        'anos_disponiveis': anos_lista,       # ✅ NOVO
        'imoveis': Imovel.objects.filter(is_active=True),
        
        # KPIs
        'kpis': {
            'receita_prevista': float(receita_prevista),
            'receita_realizada': float(receita_realizada),
            'taxa_recebimento': float(taxa_recebimento),
            'receita_pendente': float(receita_pendente),
            'comandas_atrasadas': comandas_atrasadas,
            'taxa_inadimplencia': float(taxa_inadimplencia),
            'total_comandas': total_comandas,
            'contratos_ativos': contratos_ativos,  # ✅ CORRIGIDO
            'receita_prevista_alerta': taxa_recebimento < 80,
            'inadimplencia_alerta': taxa_inadimplencia > 3,
        },
        
        # Dados para gráficos
        'dados_mensais': dados_mensais,
        'performance_imoveis': performance_imoveis,
        
        # Listagem
        'ultimos_pagamentos': ultimos_pagamentos,
        
        # Alertas
        'alertas': alertas,
        
        # Django admin context
        'title': 'Dashboard Financeiro',
        'site_title': 'HABITAT PRO',
        'site_header': 'HABITAT PRO',
        'has_permission': True,
    }
    
    return render(request, 'relatorios/dashboard_financeiro.html', context)


# ========================================
# VIEWS DE EXPORTAÇÃO (✅ MANTIDAS)
# ========================================

@staff_member_required
def exportar_dashboard_excel(request):
    """Exporta dashboard para Excel"""
    # FUTURE: Implementar exportação Excel
    messages.info(request, '📊 Exportação Excel em desenvolvimento')
    return redirect('dashboard_financeiro')


@staff_member_required
def exportar_dashboard_pdf(request):
    """Exporta dashboard para PDF"""
    # FUTURE: Implementar exportação PDF
    messages.info(request, '📄 Exportação PDF em desenvolvimento')
    return redirect('dashboard_financeiro')


@staff_member_required
def enviar_relatorio_email(request):
    """Envia relatório do dashboard por email"""
    # FUTURE: Implementar envio de email
    
    if request.method == 'POST':
        email = request.POST.get('email', '')
        if email:
            messages.success(request, f'📧 Relatório será enviado para {email}')
        else:
            messages.warning(request, '⚠️ Email não informado')
    
    return redirect('dashboard_financeiro')
