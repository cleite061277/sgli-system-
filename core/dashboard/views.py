from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from .analytics import DashboardFinancialAnalytics
import json


@staff_member_required
def dashboard_financeiro_view(request):
    """
    View principal do dashboard financeiro - Versão 2.0
    Inclui alertas, inadimplência mensal e performance de imóveis
    """
    try:
        analytics = DashboardFinancialAnalytics()
        
        # KPIs principais
        kpis = analytics.get_kpis()
        
        # Receitas 12 meses (previsto vs realizado)
        receitas = analytics.get_receitas_12_meses()
        
        # Inadimplência 12 meses
        inadimplencia = analytics.get_inadimplencia_12_meses()
        
        # Formas de pagamento
        formas = analytics.get_formas_pagamento()
        
        # Alertas críticos
        alertas = analytics.get_alertas_criticos()
        
        # Performance de imóveis
        performance = analytics.get_performance_imoveis(limite=10)
        
        # Tabelas
        pagamentos_recentes = analytics.get_pagamentos_recentes(limite=10)
        comandas_vencidas = analytics.get_comandas_vencidas(limite=20)
        previsao = analytics.get_previsao_recebimentos(dias=30)
        
        context = {
            # KPIs
            'receita_mes': kpis['receita_mes'],
            'receita_ano': kpis['receita_ano'],
            'receita_recebida': kpis['receita_recebida'],
            'contratos_ativos': kpis['contratos_ativos'],
            'taxa_inadimplencia': kpis['taxa_inadimplencia'],
            'total_inadimplencia': kpis['total_inadimplencia'],
            'taxa_ocupacao': kpis['taxa_ocupacao'],
            'total_imoveis': kpis['total_imoveis'],
            
            # Gráfico Receitas (JSON para Chart.js)
            'receitas_labels': json.dumps(receitas['labels']),
            'receitas_previsto': json.dumps(receitas['previsto']),
            'receitas_realizado': json.dumps(receitas['realizado']),
            
            # Gráfico Inadimplência (JSON para Chart.js)
            'inadimplencia_labels': json.dumps(inadimplencia['labels']),
            'inadimplencia_taxas': json.dumps(inadimplencia['taxas']),
            
            # Gráfico Formas de Pagamento (JSON para Chart.js)
            'formas_labels': json.dumps(formas['labels']),
            'formas_valores': json.dumps(formas['valores']),
            
            # Alertas
            'alertas': alertas,
            'total_alertas': len(alertas),
            
            # Performance Imóveis (JSON para Chart.js)
            'performance_imoveis': json.dumps(performance),
            
            # Tabelas
            'pagamentos_recentes': pagamentos_recentes,
            'comandas_vencidas': comandas_vencidas,
            'previsao_recebimentos': previsao['comandas'],
            'previsao_total': previsao['total'],
        }
        
        return render(request, 'admin/dashboard_financeiro.html', context)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro no dashboard financeiro: {e}", exc_info=True)
        
        # Retornar página de erro com valores padrão
        return render(request, 'admin/dashboard_financeiro.html', {
            'erro': str(e),
            'receita_mes': 0,
            'receita_ano': 0,
            'receita_recebida': 0,
            'contratos_ativos': 0,
            'taxa_inadimplencia': 0,
            'total_inadimplencia': 0,
            'taxa_ocupacao': 0,
            'total_imoveis': 0,
            'receitas_labels': '[]',
            'receitas_previsto': '[]',
            'receitas_realizado': '[]',
            'inadimplencia_labels': '[]',
            'inadimplencia_taxas': '[]',
            'formas_labels': '[]',
            'formas_valores': '[]',
            'alertas': [],
            'total_alertas': 0,
            'performance_imoveis': '[]',
            'pagamentos_recentes': [],
            'comandas_vencidas': [],
            'previsao_recebimentos': [],
            'previsao_total': 0,
        }, status=500)
