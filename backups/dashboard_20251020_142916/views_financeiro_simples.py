from rest_framework.decorators import api_view
from rest_framework.response import Response
from decimal import Decimal
from .models import Comanda
from .utils import formatar_moeda_brasileira

def calcular_valor_total_manual(comanda):
    valor_aluguel = comanda.valor_aluguel or Decimal("0.00")
    valor_condominio = comanda.valor_condominio or Decimal("0.00")
    valor_iptu = comanda.valor_iptu or Decimal("0.00")
    valor_administracao = comanda.valor_administracao or Decimal("0.00")
    outros_creditos = comanda.outros_creditos or Decimal("0.00")
    outros_debitos = comanda.outros_debitos or Decimal("0.00")
    multa = comanda.multa or Decimal("0.00")
    juros = comanda.juros or Decimal("0.00")
    desconto = comanda.desconto or Decimal("0.00")
    
    total = (valor_aluguel + valor_condominio + valor_iptu + 
             valor_administracao + outros_debitos + multa + juros - 
             outros_creditos - desconto)
    return max(total, Decimal('0.00'))

@api_view(['GET'])
def resumo_financeiro_publico(request):
    comandas = Comanda.objects.all()
    total_comandas = comandas.count()
    valor_total_cobrado = Decimal('0.00')
    
    comandas_lista = []
    for c in comandas.order_by('-created_at'):
        valor_total = calcular_valor_total_manual(c)
        valor_total_cobrado += valor_total
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
    
    return Response({
        'resumo': {
            'total_comandas': total_comandas,
            'valor_total_cobrado': formatar_moeda_brasileira(valor_total_cobrado),
        },
        'comandas': comandas_lista,
        'status': 'success'
    })
