"""
Views para Painel de WhatsApp
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
import urllib.parse

from .models import Comanda, Locacao
from .notifications.message_formatter import MessageFormatter


@login_required
def painel_whatsapp(request):
    """
    Painel principal de comandas para envio via WhatsApp
    """
    # Filtros
    mes_atual = timezone.now().date().replace(day=1)
    status_filtro = request.GET.get('status', 'TODOS')
    mes_filtro = request.GET.get('mes', mes_atual.strftime('%Y-%m'))
    
    # Parse do mês selecionado
    try:
        ano, mes = map(int, mes_filtro.split('-'))
        mes_ref = datetime(ano, mes, 1).date()
    except:
        mes_ref = mes_atual
    
    # Query base
    comandas = Comanda.objects.filter(
        mes_referencia=mes_ref
    ).select_related(
        'locacao__imovel',
        'locacao__locatario'
    ).order_by('locacao__imovel__endereco')
    
    # Aplicar filtro de status
    if status_filtro != 'TODOS':
        comandas = comandas.filter(status=status_filtro)
    
    # Estatísticas
    total_comandas = comandas.count()
    total_pendentes = comandas.filter(status='PENDING').count()
    total_pagas = comandas.filter(status='PAGA').count()
    total_vencidas = comandas.filter(
        data_vencimento__lt=timezone.now().date(),
        status__in=['PENDING', 'ATRASADA']
    ).count()
    
    # Calcular totais
    valor_total = sum(c.valor_total for c in comandas)
    valor_pago = sum(c.valor_total for c in comandas if c.status == 'PAGA')
    valor_pendente = valor_total - valor_pago
    
    context = {
        'comandas': comandas,
        'mes_selecionado': mes_ref,
        'status_filtro': status_filtro,
        'total_comandas': total_comandas,
        'total_pendentes': total_pendentes,
        'total_pagas': total_pagas,
        'total_vencidas': total_vencidas,
        'valor_total': valor_total,
        'valor_pago': valor_pago,
        'valor_pendente': valor_pendente,
        'meses_disponiveis': Comanda.objects.dates('mes_referencia', 'month', order='DESC')[:12],
    }
    
    return render(request, 'admin/whatsapp/painel.html', context)


@login_required
def gerar_mensagem_whatsapp(request, comanda_id):
    """
    Gera mensagem formatada e URL do WhatsApp para uma comanda
    """
    comanda = get_object_or_404(Comanda, id=comanda_id)
    
    # Obter locatário
    locatario = comanda.locacao.locatario if comanda.locacao else None
    
    if not locatario or not locatario.telefone:
        return JsonResponse({
            'success': False,
            'error': 'Locatário não possui telefone cadastrado'
        }, status=400)
    
    # Limpar telefone (apenas números)
    telefone_limpo = ''.join(filter(str.isdigit, locatario.telefone))
    
    # Adicionar código do país se não tiver (Brasil = 55)
    if not telefone_limpo.startswith('55'):
        telefone_limpo = '55' + telefone_limpo
    
    # Gerar URL da página da comanda (se quiser implementar página pública)
    comanda_url = request.build_absolute_uri(f'/comanda/{comanda.token}/')
    # comanda_url = None  # Agora COM página pública!
    
    # Formatar mensagem
    mensagem = MessageFormatter.formatar_mensagem_whatsapp_comanda(
        comanda, 
        comanda_url=comanda_url
    )
    
    # Gerar URL WhatsApp
    mensagem_encoded = urllib.parse.quote(mensagem)
    whatsapp_url = f'https://wa.me/{telefone_limpo}?text={mensagem_encoded}'
    
    return JsonResponse({
        'success': True,
        'whatsapp_url': whatsapp_url,
        'telefone': telefone_limpo,
        'mensagem': mensagem
    })
