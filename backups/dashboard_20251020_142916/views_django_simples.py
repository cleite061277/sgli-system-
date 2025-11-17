from django.http import JsonResponse, FileResponse, Http404
from django.conf import settings
from decimal import Decimal
from .models import Comanda
from .utils import formatar_moeda_brasileira
import os

def calcular_valor_total_manual(comanda):
    """Calcular valor total manualmente sem usar property."""
    valor_aluguel = comanda.valor_aluguel or Decimal("0.00")
    valor_condominio = comanda.valor_condominio or Decimal("0.00")
    valor_iptu = comanda.valor_iptu or Decimal("0.00")
    valor_administracao = comanda.valor_administracao or Decimal("0.00")
    outros_creditos = comanda.outros_creditos or Decimal("0.00")
    outros_debitos = comanda.outros_debitos or Decimal("0.00")
    multa = comanda.multa or Decimal("0.00")
    juros = comanda.juros or Decimal("0.00")
    desconto = comanda.desconto or Decimal("0.00")
    
    total = (
        valor_aluguel + valor_condominio + valor_iptu + 
        valor_administracao + outros_debitos + multa + juros - 
        outros_creditos - desconto
    )
    return max(total, Decimal('0.00'))

def relatorio_financeiro_django(request):
    """Relatório financeiro usando Django puro."""
    comandas = Comanda.objects.all()
    total_comandas = comandas.count()
    valor_total_cobrado = Decimal('0.00')
    
    comandas_pagas = comandas.filter(status=Comanda.StatusComanda.PAGA).count()
    comandas_pendentes = comandas.filter(status=Comanda.StatusComanda.PENDENTE).count()
    comandas_vencidas = comandas.filter(status=Comanda.StatusComanda.VENCIDA).count()
    
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
    
    return JsonResponse({
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

def lista_pagamentos(request):
    """Lista todos os pagamentos com detalhes."""
    from .models import Pagamento
    
    pagamentos = Pagamento.objects.select_related(
        'comanda', 'usuario_registro'
    ).all().order_by('-data_pagamento')[:50]
    
    lista = []
    for p in pagamentos:
        lista.append({
            'numero': p.numero_pagamento,
            'comanda': p.comanda.numero_comanda,
            'valor': formatar_moeda_brasileira(p.valor_pago),
            'data': p.data_pagamento.strftime('%d/%m/%Y'),
            'forma': p.get_forma_pagamento_display(),
            'status': p.get_status_display(),
            'usuario': p.usuario_registro.get_full_name()
        })
    
    return JsonResponse({
        'total': pagamentos.count(),
        'pagamentos': lista
    })

def download_documento(request, filename):
    """Download de documentos gerados."""
    file_path = os.path.join(settings.MEDIA_ROOT, 'documentos_gerados', filename)
    
    if os.path.exists(file_path):
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=filename
        )
    else:
        raise Http404("Documento não encontrado")

def listar_documentos(request):
    """Listar todos os documentos gerados."""
    docs_dir = os.path.join(settings.MEDIA_ROOT, 'documentos_gerados')
    
    if not os.path.exists(docs_dir):
        return JsonResponse({'documentos': [], 'total': 0})
    
    documentos = []
    for filename in sorted(os.listdir(docs_dir), reverse=True):
        if filename.endswith('.docx'):
            filepath = os.path.join(docs_dir, filename)
            size = os.path.getsize(filepath)
            
            if filename.startswith('contrato_'):
                tipo = 'Contrato'
            elif filename.startswith('recibo_'):
                tipo = 'Recibo'
            else:
                tipo = 'Documento'
            
            documentos.append({
                'nome': filename,
                'tipo': tipo,
                'tamanho': f"{size / 1024:.1f} KB",
                'url_download': f"/documentos/download/{filename}"
            })
    
    return JsonResponse({
        'total': len(documentos),
        'documentos': documentos
    })
