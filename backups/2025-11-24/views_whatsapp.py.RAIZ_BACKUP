"""
Views para Painel de Notificações WhatsApp
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import Comanda, Locacao


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
        mes_referencia=mes_ref,
        is_active=True
    ).select_related(
        'locacao__locatario',
        'locacao__imovel'
    ).order_by('data_vencimento', 'locacao__locatario__nome_razao_social')
    
    # Aplicar filtro de status
    if status_filtro != 'TODOS':
        comandas = comandas.filter(status=status_filtro)
    
    # Estatísticas
    total_comandas = comandas.count()
    total_pendentes = comandas.filter(status='PENDING').count()
    total_vencidas = comandas.filter(status='OVERDUE').count()
    total_pagas = comandas.filter(status='PAID').count()
    
    # Preparar lista de meses para o filtro (últimos 12 meses)
    meses_disponiveis = []
    for i in range(12):
        data = mes_atual - timedelta(days=30*i)
        data = data.replace(day=1)
        meses_disponiveis.append({
            'valor': data.strftime('%Y-%m'),
            'label': data.strftime('%B/%Y').capitalize()
        })
    
    context = {
        'comandas': comandas,
        'mes_ref': mes_ref,
        'status_filtro': status_filtro,
        'mes_filtro': mes_filtro,
        'meses_disponiveis': meses_disponiveis,
        'stats': {
            'total': total_comandas,
            'pendentes': total_pendentes,
            'vencidas': total_vencidas,
            'pagas': total_pagas,
        }
    }
    
    return render(request, 'core/painel_whatsapp.html', context)


@login_required
def detalhe_comanda_whatsapp(request, comanda_id):
    """
    Detalhes de uma comanda específica com mensagem formatada para WhatsApp
    """
    comanda = get_object_or_404(
        Comanda.objects.select_related(
            'locacao__locatario',
            'locacao__imovel',
            'locacao__imovel__locador'
        ),
        id=comanda_id
    )
    
    # Gerar mensagem formatada para WhatsApp
    mensagem_whatsapp = gerar_mensagem_whatsapp(comanda)
    
    context = {
        'comanda': comanda,
        'mensagem_whatsapp': mensagem_whatsapp,
    }
    
    return render(request, 'core/detalhe_comanda_whatsapp.html', context)


def gerar_mensagem_whatsapp(comanda):
    """
    Gera mensagem formatada para WhatsApp
    """
    locatario = comanda.locacao.locatario
    imovel = comanda.locacao.imovel
    
    # Determinar saudação
    if comanda.status == 'PAID':
        mensagem = f"✅ *PAGAMENTO CONFIRMADO*\n\n"
    elif comanda.is_vencida:
        mensagem = f"⚠️ *AVISO DE VENCIMENTO*\n\n"
    else:
        mensagem = f"📋 *COMANDA DE ALUGUEL*\n\n"
    
    # Dados do locatário
    mensagem += f"*Locatário:* {locatario.nome_razao_social}\n"
    mensagem += f"*Imóvel:* {imovel.endereco}, {imovel.numero}\n"
    mensagem += f"*Código:* {imovel.codigo_imovel}\n\n"
    
    # Dados da comanda
    mensagem += f"━━━━━━━━━━━━━━━━━━━\n"
    mensagem += f"*REFERÊNCIA:* {comanda.mes_referencia.strftime('%m/%Y')}\n"
    mensagem += f"*Nº COMANDA:* {comanda.numero_comanda}\n"
    mensagem += f"*VENCIMENTO:* {comanda.data_vencimento.strftime('%d/%m/%Y')}\n"
    mensagem += f"━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Detalhamento de valores
    mensagem += f"*VALORES:*\n"
    mensagem += f"• Aluguel: R$ {comanda.valor_aluguel:,.2f}\n".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    if comanda.valor_condominio > 0:
        mensagem += f"• Condomínio: R$ {comanda.valor_condominio:,.2f}\n".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    if comanda.valor_iptu > 0:
        mensagem += f"• IPTU: R$ {comanda.valor_iptu:,.2f}\n".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    if comanda.outros_debitos > 0:
        mensagem += f"• Outros débitos: R$ {comanda.outros_debitos:,.2f}\n".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    if comanda.multa > 0:
        mensagem += f"• Multa: R$ {comanda.multa:,.2f}\n".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    if comanda.juros > 0:
        mensagem += f"• Juros: R$ {comanda.juros:,.2f}\n".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    if comanda.desconto > 0:
        mensagem += f"• Desconto: -R$ {comanda.desconto:,.2f}\n".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    mensagem += f"\n*TOTAL: R$ {comanda.valor_total:,.2f}*\n".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # Status
    if comanda.status == 'PAID':
        mensagem += f"\n✅ Status: PAGO em {comanda.data_pagamento.strftime('%d/%m/%Y')}\n"
    elif comanda.is_vencida:
        dias_atraso = comanda.dias_atraso
        mensagem += f"\n⚠️ Status: VENCIDO há {dias_atraso} dia(s)\n"
    else:
        dias_restantes = (comanda.data_vencimento - timezone.now().date()).days
        mensagem += f"\n⏰ Status: PENDENTE ({dias_restantes} dias para vencimento)\n"
    
    # Rodapé
    mensagem += f"\n━━━━━━━━━━━━━━━━━━━\n"
    mensagem += f"📞 Dúvidas? Entre em contato.\n"
    mensagem += f"_Mensagem gerada automaticamente_"
    
    return mensagem


@login_required
def api_mensagem_comanda(request, comanda_id):
    """
    API endpoint que retorna a mensagem formatada em JSON
    """
    comanda = get_object_or_404(
        Comanda.objects.select_related(
            'locacao__locatario',
            'locacao__imovel'
        ),
        id=comanda_id
    )
    
    mensagem = gerar_mensagem_whatsapp(comanda)
    
    return JsonResponse({
        'mensagem': mensagem,
        'comanda_id': str(comanda.id),
        'numero_comanda': comanda.numero_comanda,
        'telefone': comanda.locacao.locatario.telefone,
        'nome_locatario': comanda.locacao.locatario.nome_razao_social,
    })
