"""
Advanced reporting system for SGLI.
Generates financial and operational reports.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from django.db.models import Q, Sum, Count, Avg, Case, When, Value, DecimalField
from django.db.models.functions import TruncMonth, TruncYear, Coalesce
from django.utils import timezone
from .models import Locacao, Comanda, Pagamento, Imovel, Locador, Locatario
from .utils import formatar_moeda_brasileira

class RelatorioFinanceiro:
    """Financial reporting system."""
    
    def __init__(self, data_inicio: datetime = None, data_fim: datetime = None):
        self.data_inicio = data_inicio or timezone.now() - timedelta(days=365)
        self.data_fim = data_fim or timezone.now()
    
    def resumo_geral(self) -> Dict[str, Any]:
        """Generate general financial summary."""
        # Comandas no período
        comandas = Comanda.objects.filter(
            data_vencimento__range=[self.data_inicio.date(), self.data_fim.date()]
        )
        
        # Pagamentos no período
        pagamentos = Pagamento.objects.filter(
            data_pagamento__range=[self.data_inicio.date(), self.data_fim.date()],
            status=Pagamento.StatusPagamento.CONFIRMADO
        )
        
        resumo = {
            # Comandas
            'total_comandas': comandas.count(),
            'valor_total_cobrado': comandas.aggregate(
                total=Coalesce(Sum('valor_total'), Decimal('0.00'))
            )['total'],
            'comandas_pagas': comandas.filter(status=Comanda.StatusComanda.PAGA).count(),
            'comandas_pendentes': comandas.filter(status=Comanda.StatusComanda.PENDENTE).count(),
            'comandas_vencidas': comandas.filter(status=Comanda.StatusComanda.VENCIDA).count(),
            
            # Pagamentos
            'total_pagamentos': pagamentos.count(),
            'valor_total_recebido': pagamentos.aggregate(
                total=Coalesce(Sum('valor_pago'), Decimal('0.00'))
            )['total'],
            
            # Inadimplência
            'valor_em_aberto': comandas.filter(
                status__in=[Comanda.StatusComanda.PENDENTE, Comanda.StatusComanda.VENCIDA]
            ).aggregate(
                total=Coalesce(Sum('valor_total'), Decimal('0.00'))
            )['total'],
            
            # Locações ativas
            'locacoes_ativas': Locacao.objects.filter(status=Locacao.StatusLocacao.ATIVO).count(),
            'imoveis_ocupados': Imovel.objects.filter(status=Imovel.StatusImovel.OCUPADO).count(),
            'imoveis_disponiveis': Imovel.objects.filter(status=Imovel.StatusImovel.DISPONIVEL).count(),
        }
        
        # Calcular taxa de inadimplência
        if resumo['valor_total_cobrado'] > 0:
            resumo['taxa_inadimplencia'] = (
                resumo['valor_em_aberto'] / resumo['valor_total_cobrado'] * 100
            )
        else:
            resumo['taxa_inadimplencia'] = Decimal('0.00')
        
        # Formatação
        for key, value in resumo.items():
            if key.startswith('valor_') and isinstance(value, (Decimal, float, int)):
                resumo[f"{key}_formatado"] = formatar_moeda_brasileira(value)
        
        return resumo
    
    def evolucao_mensal(self) -> List[Dict[str, Any]]:
        """Generate monthly evolution report."""
        comandas_mensais = Comanda.objects.filter(
            data_vencimento__range=[self.data_inicio.date(), self.data_fim.date()]
        ).annotate(
            mes=TruncMonth('data_vencimento')
        ).values('mes').annotate(
            total_comandas=Count('id'),
            valor_cobrado=Coalesce(Sum('valor_total'), Decimal('0.00')),
            comandas_pagas=Count(Case(When(status=Comanda.StatusComanda.PAGA, then=1))),
            valor_pago=Coalesce(Sum('valor_pago'), Decimal('0.00'))
        ).order_by('mes')
        
        return [
            {
                **item,
                'mes_formatado': item['mes'].strftime('%m/%Y'),
                'valor_cobrado_formatado': formatar_moeda_brasileira(item['valor_cobrado']),
                'valor_pago_formatado': formatar_moeda_brasileira(item['valor_pago']),
                'taxa_cobranca': (
                    item['valor_pago'] / item['valor_cobrado'] * 100 
                    if item['valor_cobrado'] > 0 else 0
                )
            }
            for item in comandas_mensais
        ]
    
    def ranking_imoveis(self) -> List[Dict[str, Any]]:
        """Generate property ranking by revenue."""
        ranking = Imovel.objects.annotate(
            total_arrecadado=Coalesce(
                Sum('locacoes__comandas__valor_pago'), 
                Decimal('0.00')
            ),
            total_comandas=Count('locacoes__comandas'),
            ultima_locacao=Max('locacoes__created_at')
        ).order_by('-total_arrecadado')[:10]
        
        return [
            {
                'codigo': imovel.codigo_imovel,
                'endereco': imovel.endereco_completo,
                'tipo': imovel.get_tipo_imovel_display(),
                'total_arrecadado': imovel.total_arrecadado,
                'total_arrecadado_formatado': formatar_moeda_brasileira(imovel.total_arrecadado),
                'total_comandas': imovel.total_comandas,
                'valor_aluguel_formatado': formatar_moeda_brasileira(imovel.valor_aluguel),
                'status': imovel.get_status_display()
            }
            for imovel in ranking
        ]
    
    def inadimplencia_detalhada(self) -> Dict[str, Any]:
        """Generate detailed delinquency report."""
        comandas_vencidas = Comanda.objects.filter(
            data_vencimento__lt=timezone.now().date(),
            status__in=[Comanda.StatusComanda.PENDENTE, Comanda.StatusComanda.VENCIDA]
        ).select_related('locacao', 'locacao__locatario', 'locacao__imovel')
        
        # Agrupar por faixas de atraso
        hoje = timezone.now().date()
        faixas = {
            '0-30': comandas_vencidas.filter(
                data_vencimento__gte=hoje - timedelta(days=30)
            ),
            '31-60': comandas_vencidas.filter(
                data_vencimento__lt=hoje - timedelta(days=30),
                data_vencimento__gte=hoje - timedelta(days=60)
            ),
            '61-90': comandas_vencidas.filter(
                data_vencimento__lt=hoje - timedelta(days=60),
                data_vencimento__gte=hoje - timedelta(days=90)
            ),
            '90+': comandas_vencidas.filter(
                data_vencimento__lt=hoje - timedelta(days=90)
            )
        }
        
        relatorio_faixas = {}
        for faixa, queryset in faixas.items():
            valor_total = queryset.aggregate(
                total=Coalesce(Sum('valor_total'), Decimal('0.00'))
            )['total']
            
            relatorio_faixas[faixa] = {
                'quantidade': queryset.count(),
                'valor_total': valor_total,
                'valor_formatado': formatar_moeda_brasileira(valor_total),
                'comandas': [
                    {
                        'numero': c.numero_comanda,
                        'locatario': c.locacao.locatario.nome_razao_social,
                        'imovel': c.locacao.imovel.endereco_completo,
                        'valor': formatar_moeda_brasileira(c.valor_total),
                        'dias_atraso': (hoje - c.data_vencimento).days,
                        'data_vencimento': c.data_vencimento.strftime('%d/%m/%Y')
                    }
                    for c in queryset.order_by('-data_vencimento')[:5]
                ]
            }
        
        return relatorio_faixas

class RelatorioOperacional:
    """Operational reporting system."""
    
    def dashboard_metricas(self) -> Dict[str, Any]:
        """Generate dashboard metrics."""
        hoje = timezone.now().date()
        inicio_mes = hoje.replace(day=1)
        
        return {
            'ocupacao': {
                'total_imoveis': Imovel.objects.count(),
                'imoveis_ocupados': Imovel.objects.filter(
                    status=Imovel.StatusImovel.OCUPADO
                ).count(),
                'imoveis_disponiveis': Imovel.objects.filter(
                    status=Imovel.StatusImovel.DISPONIVEL
                ).count(),
                'taxa_ocupacao': self._calcular_taxa_ocupacao()
            },
            'financeiro_mes': {
                'comandas_mes': Comanda.objects.filter(
                    data_vencimento__gte=inicio_mes
                ).count(),
                'valor_cobrado_mes': Comanda.objects.filter(
                    data_vencimento__gte=inicio_mes
                ).aggregate(
                    total=Coalesce(Sum('valor_total'), Decimal('0.00'))
                )['total'],
                'pagamentos_mes': Pagamento.objects.filter(
                    data_pagamento__gte=inicio_mes,
                    status=Pagamento.StatusPagamento.CONFIRMADO
                ).count(),
                'valor_recebido_mes': Pagamento.objects.filter(
                    data_pagamento__gte=inicio_mes,
                    status=Pagamento.StatusPagamento.CONFIRMADO
                ).aggregate(
                    total=Coalesce(Sum('valor_pago'), Decimal('0.00'))
                )['total']
            },
            'alertas': self._gerar_alertas()
        }
    
    def _calcular_taxa_ocupacao(self) -> float:
        """Calculate occupancy rate."""
        total = Imovel.objects.count()
        if total == 0:
            return 0.0
        ocupados = Imovel.objects.filter(status=Imovel.StatusImovel.OCUPADO).count()
        return (ocupados / total) * 100
    
    def _gerar_alertas(self) -> List[Dict[str, Any]]:
        """Generate system alerts."""
        alertas = []
        hoje = timezone.now().date()
        
        # Comandas vencendo nos próximos 5 dias
        comandas_vencendo = Comanda.objects.filter(
            data_vencimento__range=[hoje, hoje + timedelta(days=5)],
            status=Comanda.StatusComanda.PENDENTE
        ).count()
        
        if comandas_vencendo > 0:
            alertas.append({
                'tipo': 'warning',
                'titulo': 'Comandas Vencendo',
                'mensagem': f'{comandas_vencendo} comando(s) vencem nos próximos 5 dias',
                'quantidade': comandas_vencendo
            })
        
        # Comandas vencidas
        comandas_vencidas = Comanda.objects.filter(
            data_vencimento__lt=hoje,
            status__in=[Comanda.StatusComanda.PENDENTE, Comanda.StatusComanda.VENCIDA]
        ).count()
        
        if comandas_vencidas > 0:
            alertas.append({
                'tipo': 'danger',
                'titulo': 'Comandas Vencidas',
                'mensagem': f'{comandas_vencidas} comando(s) em atraso',
                'quantidade': comandas_vencidas
            })
        
        # Contratos vencendo em 60 dias
        contratos_vencendo = Locacao.objects.filter(
            data_fim__range=[hoje, hoje + timedelta(days=60)],
            status=Locacao.StatusLocacao.ATIVO
        ).count()
        
        if contratos_vencendo > 0:
            alertas.append({
                'tipo': 'info',
                'titulo': 'Contratos Vencendo',
                'mensagem': f'{contratos_vencendo} contrato(s) vencem em até 60 dias',
                'quantidade': contratos_vencendo
            })
        
        return alertas

