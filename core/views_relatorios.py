from django.shortcuts import render
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from core.models import Comanda, Locacao, Imovel, Pagamento


def dashboard_relatorios(request):
    """Dashboard principal com indicadores"""
    hoje = timezone.now().date()
    mes_atual = hoje.replace(day=1)
    
    # Indicadores principais
    total_imoveis = Imovel.objects.count()
    imoveis_ocupados = Locacao.objects.filter(status='ativa').count()
    taxa_ocupacao = (imoveis_ocupados / total_imoveis * 100) if total_imoveis > 0 else 0
    
    # Receitas do mês
    receita_mes = Comanda.objects.filter(
        mes_referencia=mes_atual,
        status='paga'
    ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
    
    # Inadimplência
    comandas_vencidas = Comanda.objects.filter(
        status='vencida',
        data_vencimento__lt=hoje
    )
    valor_inadimplencia = sum(c.valor_total for c in comandas_vencidas)
    qtd_inadimplentes = comandas_vencidas.count()
    
    # Receita esperada vs realizada
    comandas_mes = Comanda.objects.filter(mes_referencia=mes_atual)
    receita_esperada = sum(c.valor_total for c in comandas_mes)
    percentual_recebido = (float(receita_mes) / float(receita_esperada) * 100) if receita_esperada > 0 else 0
    
    # Últimas 6 meses
    meses_anteriores = []
    for i in range(6, 0, -1):
        mes = hoje - timedelta(days=30*i)
        mes_ref = mes.replace(day=1)
        receita = Comanda.objects.filter(
            mes_referencia=mes_ref,
            status='paga'
        ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
        
        meses_anteriores.append({
            'mes': mes_ref.strftime('%b/%y'),
            'receita': float(receita)
        })
    
    context = {
        'total_imoveis': total_imoveis,
        'imoveis_ocupados': imoveis_ocupados,
        'taxa_ocupacao': round(taxa_ocupacao, 1),
        'receita_mes': receita_mes,
        'receita_esperada': receita_esperada,
        'percentual_recebido': round(percentual_recebido, 1),
        'valor_inadimplencia': valor_inadimplencia,
        'qtd_inadimplentes': qtd_inadimplentes,
        'meses_anteriores': meses_anteriores,
    }
    
    return render(request, 'relatorios/dashboard.html', context)


def relatorio_inadimplencia(request):
    """Relatório detalhado de inadimplência"""
    hoje = timezone.now().date()
    
    comandas_vencidas = Comanda.objects.filter(
        status__in=['vencida', 'pendente'],
        data_vencimento__lt=hoje
    ).select_related('locacao', 'locacao__imovel', 'locacao__locatario').order_by('data_vencimento')
    
    total_inadimplencia = sum(c.valor_total for c in comandas_vencidas)
    
    context = {
        'comandas': comandas_vencidas,
        'total': total_inadimplencia,
        'data_geracao': hoje,
    }
    
    return render(request, 'relatorios/inadimplencia.html', context)


def relatorio_imoveis(request):
    """Relatório de performance por imóvel"""
    imoveis = Imovel.objects.all()
    
    dados_imoveis = []
    for imovel in imoveis:
        locacao_ativa = imovel.locacoes.filter(status='ativa').first()
        
        # Receita do imóvel (últimos 12 meses)
        receita_12m = Comanda.objects.filter(
            locacao__imovel=imovel,
            status='paga',
            mes_referencia__gte=timezone.now().date() - timedelta(days=365)
        ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
        
        dados_imoveis.append({
            'imovel': imovel,
            'locacao': locacao_ativa,
            'receita_12m': receita_12m,
            'status': imovel.status,
        })
    
    context = {
        'dados_imoveis': dados_imoveis,
    }
    
    return render(request, 'relatorios/imoveis.html', context)
