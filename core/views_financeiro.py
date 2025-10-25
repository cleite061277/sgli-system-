from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from decimal import Decimal
from .models import Comanda
from .utils import formatar_moeda_brasileira

@api_view(['GET'])
def resumo_financeiro(request):
    """Endpoint para relatório financeiro básico."""
    comandas = Comanda.objects.all()
    
    # Calcular totais básicos - acessando property corretamente
    total_comandas = comandas.count()
    valor_total_cobrado = Decimal('0.00')
    
    # Calcular total de forma segura
    for c in comandas:
        try:
            # Acessar valor_total como property (sem parênteses)
            valor_total_cobrado += c.valor_total
        except Exception as e:
            print(f"Erro ao acessar valor_total de {c.numero_comanda}: {e}")
            continue
    
    # Status das comandas
    comandas_pagas = comandas.filter(status=Comanda.StatusComanda.PAGA).count()
    comandas_pendentes = comandas.filter(status=Comanda.StatusComanda.PENDENTE).count()
    comandas_vencidas = comandas.filter(status=Comanda.StatusComanda.VENCIDA).count()
    
    # Lista das comandas com informações básicas
    comandas_lista = []
    for c in comandas.order_by('-created_at')[:15]:
        try:
            valor_total = c.valor_total  # Property access
            valor_pago = c.valor_pago or Decimal('0.00')
            saldo = valor_pago - valor_total
            
            comandas_lista.append({
                'numero': c.numero_comanda,
                'locatario': c.locacao.locatario.nome_razao_social,
                'valor_total': formatar_moeda_brasileira(valor_total),
                'valor_pago': formatar_moeda_brasileira(valor_pago),
                'saldo': formatar_moeda_brasileira(abs(saldo)),
                'tipo_saldo': 'credor' if saldo > 0 else 'devedor' if saldo < 0 else 'zerado',
                'status': c.get_status_display(),
                'referencia': f"{c.mes_referencia:02d}/{c.ano_referencia}"
            })
        except Exception as e:
            print(f"Erro ao processar comanda {c.numero_comanda}: {e}")
            continue
    
    return Response({
        'resumo': {
            'total_comandas': total_comandas,
            'valor_total_cobrado': formatar_moeda_brasileira(valor_total_cobrado),
            'comandas_pagas': comandas_pagas,
            'comandas_pendentes': comandas_pendentes,
            'comandas_vencidas': comandas_vencidas
        },
        'comandas': comandas_lista,
        'status': 'success'
    })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_financeiro(request):
    """Página do dashboard financeiro."""
    return render(request, 'dashboard/financeiro.html')

@api_view(['GET'])

@api_view(['GET'])
def detalhe_comanda(request, numero_comanda):
    """Endpoint para detalhes específicos de uma comanda."""
    try:
        comanda = Comanda.objects.get(numero_comanda=numero_comanda)
        
        # Calcular valor total manualmente
        valor_total = calcular_valor_total_manual(comanda)
        valor_pago = comanda.valor_pago or Decimal('0.00')
        
        return Response({
            'numero': comanda.numero_comanda,
            'status': comanda.get_status_display(),
            'locatario': comanda.locacao.locatario.nome_razao_social,
            'imovel': comanda.locacao.imovel.endereco_completo,
            'valor_total': formatar_moeda_brasileira(valor_total),
            'valor_pago': formatar_moeda_brasileira(valor_pago),
            'saldo': formatar_moeda_brasileira(abs(valor_total - valor_pago)),
            'data_vencimento': comanda.data_vencimento.strftime('%d/%m/%Y')
        })
    except Comanda.DoesNotExist:
        return Response({'error': 'Comanda não encontrada'}, status=404)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_documentos(request):
    """Página do dashboard de documentos."""
    return render(request, 'dashboard/documentos.html')
