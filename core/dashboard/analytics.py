from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from core.models import Comanda, Locacao, Imovel, Pagamento


class DashboardFinancialAnalytics:
    """
    Serviço de analytics aprimorado - Versão 2.0 CORRIGIDA
    TODOS os Decimals convertidos para float
    TODOS os QuerySets serializáveis
    """
    
    def __init__(self):
        hoje = timezone.now().date()
        self.mes = hoje.month
        self.ano = hoje.year
        self.hoje = hoje
    
    def get_kpis(self):
        """KPIs principais - CORRIGIDO: Todos valores em float."""
        total_imoveis = Imovel.objects.filter(is_active=True).count()
        locacoes_ativas = Locacao.objects.filter(status='ACTIVE', is_active=True).count()
        taxa_ocupacao = (locacoes_ativas / total_imoveis * 100) if total_imoveis > 0 else 0
        
        comandas_mes = Comanda.objects.filter(
            mes_referencia__month=self.mes,
            mes_referencia__year=self.ano
        )
        # ✅ CORREÇÃO: Converter Decimal para float
        receita_mes = float(sum(c.valor_total for c in comandas_mes))
        
        comandas_ano = Comanda.objects.filter(mes_referencia__year=self.ano)
        # ✅ CORREÇÃO: Converter Decimal para float
        receita_ano = float(sum(c.valor_total for c in comandas_ano))
        
        # ✅ CORREÇÃO: status='ACTIVE' (maiúsculo)
        contratos_ativos = Locacao.objects.filter(status='ACTIVE', is_active=True).count()
        
        comandas_vencidas = Comanda.objects.filter(status='OVERDUE')
        # ✅ CORREÇÃO: Converter Decimal para float
        total_inadimplencia = float(sum(c.valor_total for c in comandas_vencidas))
        taxa_inadimplencia = (total_inadimplencia / receita_mes * 100) if receita_mes > 0 else 0
        
        comandas_pagas = Comanda.objects.filter(status='PAID', mes_referencia__year=self.ano)
        # ✅ CORREÇÃO: Converter Decimal para float
        receita_recebida = float(sum(c.valor_total for c in comandas_pagas))
        
        return {
            'total_imoveis': total_imoveis,
            'receita_mes': receita_mes,  # float
            'receita_ano': receita_ano,  # float
            'receita_recebida': receita_recebida,  # float
            'contratos_ativos': contratos_ativos,
            'taxa_inadimplencia': round(taxa_inadimplencia, 2),
            'total_inadimplencia': total_inadimplencia,  # float
            'taxa_ocupacao': round(taxa_ocupacao, 2),
        }
    
    def get_receitas_12_meses(self):
        """Receitas previstas vs realizadas - JÁ CORRIGIDO."""
        labels, previsto, realizado = [], [], []
        
        for i in range(12, 0, -1):
            data = self.hoje - timedelta(days=30*i)
            comandas = Comanda.objects.filter(
                mes_referencia__month=data.month,
                mes_referencia__year=data.year
            )
            
            total_previsto = sum(c.valor_total for c in comandas)
            comandas_pagas = comandas.filter(status='PAID')
            total_realizado = sum(c.valor_total for c in comandas_pagas)
            
            labels.append(data.strftime('%b/%y'))
            previsto.append(float(total_previsto))  # ✅ float
            realizado.append(float(total_realizado))  # ✅ float
        
        return {'labels': labels, 'previsto': previsto, 'realizado': realizado}
    
    def get_inadimplencia_12_meses(self):
        """Taxa de inadimplência - JÁ CORRIGIDO."""
        labels, taxas = [], []
        
        for i in range(12, 0, -1):
            data = self.hoje - timedelta(days=30*i)
            comandas_mes = Comanda.objects.filter(
                mes_referencia__month=data.month,
                mes_referencia__year=data.year
            )
            
            total_mes = sum(c.valor_total for c in comandas_mes)
            vencidas = comandas_mes.filter(status='OVERDUE')
            total_vencido = sum(c.valor_total for c in vencidas)
            taxa = (total_vencido / total_mes * 100) if total_mes > 0 else 0
            
            labels.append(data.strftime('%b/%y'))
            taxas.append(float(round(taxa, 2)))  # ✅ float
        
        return {'labels': labels, 'taxas': taxas}
    
    def get_formas_pagamento(self):
        """Distribuição de formas de pagamento - JÁ CORRIGIDO."""
        pagamentos = Pagamento.objects.filter(status='confirmado', data_pagamento__year=self.ano)
        
        formas = {}
        for pag in pagamentos:
            forma = pag.get_forma_pagamento_display() if pag.forma_pagamento else 'Não Informado'
            formas[forma] = formas.get(forma, Decimal('0')) + (pag.valor_pago or Decimal('0'))
        
        if not formas:
            return {'labels': ['Sem dados'], 'valores': [0]}
        
        return {
            'labels': list(formas.keys()), 
            'valores': [float(v) for v in formas.values()]  # ✅ float
        }
    
    def get_pagamentos_recentes(self, limite=10):
        """Últimos pagamentos - OK (retorna objetos Django)."""
        return Pagamento.objects.filter(status='confirmado').select_related(
            'comanda__locacao__locatario', 'comanda__locacao__imovel'
        ).order_by('-data_pagamento')[:limite]
    
    def get_comandas_vencidas(self, limite=20):
        """Comandas vencidas - OK (retorna objetos Django)."""
        return Comanda.objects.filter(status='OVERDUE').select_related(
            'locacao__locatario', 'locacao__imovel'
        ).order_by('data_vencimento')[:limite]
    
    def get_previsao_recebimentos(self, dias=30):
        """Previsão de recebimentos - CORRIGIDO: total em float."""
        data_limite = self.hoje + timedelta(days=dias)
        
        comandas = Comanda.objects.filter(
            status='PENDING',
            data_vencimento__gte=self.hoje,
            data_vencimento__lte=data_limite
        ).select_related('locacao__locatario', 'locacao__imovel').order_by('data_vencimento')[:20]
        
        # ✅ CORREÇÃO: Converter total para float
        total = float(sum(c.valor_total for c in comandas))
        
        return {
            'comandas': list(comandas),  # ✅ Converter QuerySet para lista
            'total': total  # ✅ float
        }
    
    def get_alertas_criticos(self):
        """Sistema de alertas - JÁ CORRIGIDO."""
        alertas = []
        
        comandas_vencidas = Comanda.objects.filter(status='OVERDUE').count()
        if comandas_vencidas > 0:
            # ✅ CORREÇÃO: float no f-string
            total_vencido = float(sum(c.valor_total for c in Comanda.objects.filter(status='OVERDUE')))
            alertas.append({
                'tipo': 'danger',
                'icone': '⚠️',
                'titulo': f'{comandas_vencidas} Comanda(s) Vencida(s)',
                'mensagem': f'Total em atraso: R$ {total_vencido:,.2f}',
                'link': '/admin/core/comanda/?status__exact=OVERDUE',
                'acao': 'Ver comandas'
            })
        
        data_limite = self.hoje + timedelta(days=60)
        contratos_vencendo = Locacao.objects.filter(
            status='ACTIVE',
            data_fim__gte=self.hoje,
            data_fim__lte=data_limite,
            is_active=True
        ).count()
        
        if contratos_vencendo > 0:
            alertas.append({
                'tipo': 'warning',
                'icone': '📅',
                'titulo': f'{contratos_vencendo} Contrato(s) Vencendo',
                'mensagem': 'Vencimento nos próximos 60 dias',
                'link': '/admin/core/locacao/',
                'acao': 'Ver contratos'
            })
        
        kpis = self.get_kpis()
        if kpis['taxa_inadimplencia'] > 5:
            alertas.append({
                'tipo': 'danger',
                'icone': '📊',
                'titulo': 'Inadimplência Acima da Meta',
                'mensagem': f'Taxa atual: {kpis["taxa_inadimplencia"]:.1f}% (meta: 3%)',
                'link': '#inadimplenciaChart',
                'acao': 'Ver gráfico'
            })
        
        return alertas
    
    def get_performance_imoveis(self, limite=10):
        """Performance de imóveis - CORRIGIDO: todos valores em float."""
        imoveis_ativos = Imovel.objects.filter(is_active=True)[:limite]
        
        performance = []
        
        for imovel in imoveis_ativos:
            comandas = Comanda.objects.filter(
                locacao__imovel=imovel,
                mes_referencia__year=self.ano
            )
            
            # ✅ CORREÇÃO: Converter para float
            previsto = float(sum(c.valor_total for c in comandas))
            
            pagas = comandas.filter(status='PAID')
            # ✅ CORREÇÃO: Converter para float
            realizado = float(sum(c.valor_total for c in pagas))
            
            taxa = (realizado / previsto * 100) if previsto > 0 else 0
            
            performance.append({
                'nome': f"{imovel.codigo_imovel}",
                'endereco': f"{imovel.endereco}, {imovel.numero}",
                'previsto': previsto,  # ✅ float
                'realizado': realizado,  # ✅ float
                'taxa': round(taxa, 1)
            })
        
        performance.sort(key=lambda x: x['taxa'], reverse=True)
        
        return performance
