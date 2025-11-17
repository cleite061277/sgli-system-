"""
View para geração em massa de comandas via interface web
Arquivo: core/views_gerar_comandas.py

Autor: HABITAT PRO System
Data: 06/10/2025
"""

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import calendar

from .models import Locacao, Comanda, ConfiguracaoSistema, LogGeracaoComandas


@staff_member_required
def gerar_comandas_view(request):
    """
    View para gerar comandas em massa via interface web.
    Acessível apenas para usuários staff.
    """
    
    # Calcular opções de meses (próximos 3 meses)
    hoje = timezone.now().date()
    mes_atual = hoje.replace(day=1)
    
    opcoes_meses = []
    for i in range(3):
        mes = mes_atual + relativedelta(months=i)
        opcoes_meses.append({
            'valor': mes.strftime('%Y-%m'),
            'label': mes.strftime('%B/%Y').capitalize(),
            'data': mes
        })
    
    # Buscar locações ativas
    locacoes_ativas = Locacao.objects.filter(
        status='ACTIVE',
        is_active=True
    ).select_related('imovel', 'locatario')
    
    # Obter configuração
    config = ConfiguracaoSistema.get_config()
    
    context = {
        'opcoes_meses': opcoes_meses,
        'total_locacoes': locacoes_ativas.count(),
        'locacoes': locacoes_ativas,
        'config': config,
        'hoje': hoje,
    }
    
    # Se for POST, processar geração
    if request.method == 'POST':
        mes_selecionado = request.POST.get('mes_referencia')
        confirmar = request.POST.get('confirmar') == 'sim'
        
        if not mes_selecionado:
            messages.error(request, '❌ Selecione um mês de referência!')
            return render(request, 'core/gerar_comandas.html', context)
        
        try:
            mes_referencia = datetime.strptime(mes_selecionado, '%Y-%m').date()
        except ValueError:
            messages.error(request, '❌ Formato de data inválido!')
            return render(request, 'core/gerar_comandas.html', context)
        
        # Verificar comandas existentes
        comandas_existentes = Comanda.objects.filter(
            mes_referencia=mes_referencia
        ).count()
        
        # Se não confirmou e já existem comandas, mostrar aviso
        if comandas_existentes > 0 and not confirmar:
            context.update({
                'mes_selecionado': mes_selecionado,
                'mes_selecionado_label': mes_referencia.strftime('%B/%Y').capitalize(),
                'comandas_existentes': comandas_existentes,
                'mostrar_confirmacao': True,
            })
            messages.warning(
                request,
                f'⚠️ Já existem {comandas_existentes} comanda(s) para {mes_referencia.strftime("%B/%Y")}. '
                'Confirme para criar novas comandas (duplicatas serão ignoradas).'
            )
            return render(request, 'core/gerar_comandas.html', context)
        
        # Processar geração
        resultado = processar_geracao_comandas(
            mes_referencia=mes_referencia,
            locacoes=locacoes_ativas,
            config=config,
            usuario=request.user
        )
        
        # Mostrar mensagens
        if resultado['criadas'] > 0:
            messages.success(
                request,
                f'✅ {resultado["criadas"]} comanda(s) criada(s) com sucesso para {mes_referencia.strftime("%B/%Y")}!'
            )
        
        if resultado['duplicadas'] > 0:
            messages.info(
                request,
                f'ℹ️ {resultado["duplicadas"]} comanda(s) já existiam e foram ignoradas.'
            )
        
        if resultado['erros']:
            messages.error(
                request,
                f'❌ {len(resultado["erros"])} erro(s) encontrado(s). Verifique os logs.'
            )
        
        # Adicionar resultado ao contexto
        context['resultado'] = resultado
    
    return render(request, 'core/gerar_comandas.html', context)


def processar_geracao_comandas(mes_referencia, locacoes, config, usuario):
    """
    Processa a geração em massa de comandas.
    
    Args:
        mes_referencia: Data do mês de referência (primeiro dia)
        locacoes: QuerySet de locações ativas
        config: ConfiguracaoSistema
        usuario: Usuario que está gerando
    
    Returns:
        dict com resultado da operação
    """
    
    criadas = 0
    duplicadas = 0
    erros = []
    comandas_criadas = []
    
    dia_padrao = config.dia_vencimento_padrao
    
    for locacao in locacoes:
        try:
            # Verificar duplicata
            if Comanda.objects.filter(
                locacao=locacao,
                mes_referencia=mes_referencia
            ).exists():
                duplicadas += 1
                continue
            
            # Obter dia de vencimento
            dia_vencimento = getattr(locacao, 'dia_vencimento', None) or dia_padrao
            
            # Ajustar para último dia do mês se necessário
            ultimo_dia = calendar.monthrange(
                mes_referencia.year,
                mes_referencia.month
            )[1]
            
            if dia_vencimento > ultimo_dia:
                dia_vencimento = ultimo_dia
            
            data_vencimento = mes_referencia.replace(day=dia_vencimento)
            
            # Obter valores
            valor_aluguel = locacao.valor_aluguel
            valor_condominio = getattr(locacao.imovel, 'valor_condominio', Decimal('0.00')) or Decimal('0.00')
            
            # Criar comanda dentro de transação
            with transaction.atomic():
                comanda = Comanda.objects.create(
                    locacao=locacao,
                    mes_referencia=mes_referencia,
                    ano_referencia=mes_referencia.year,
                    data_vencimento=data_vencimento,
                    valor_aluguel=valor_aluguel,
                    valor_condominio=valor_condominio,
                    valor_iptu=Decimal('0.00'),
                    valor_administracao=Decimal('0.00'),
                    outros_creditos=Decimal('0.00'),
                    outros_debitos=Decimal('0.00'),
                    multa=Decimal('0.00'),
                    juros=Decimal('0.00'),
                    desconto=Decimal('0.00'),
                    status='PENDING',
                    observacoes=f'Gerada via interface web por {usuario.get_full_name() or usuario.username} em {timezone.now().strftime("%d/%m/%Y %H:%M")}'
                )
                
                comandas_criadas.append({
                    'numero': comanda.numero_comanda,
                    'locacao': str(locacao),
                    'valor_total': comanda.valor_total,
                    'vencimento': data_vencimento,
                })
                
                criadas += 1
                
        except Exception as e:
            erro_msg = f'Locação {locacao.numero_contrato}: {str(e)}'
            erros.append(erro_msg)
    
    # Registrar log
    LogGeracaoComandas.objects.create(
        mes_referencia=mes_referencia,
        comandas_geradas=criadas,
        comandas_duplicadas=duplicadas,
        locacoes_processadas=locacoes.count(),
        sucesso=len(erros) == 0,
        mensagem=f'{criadas} comandas criadas via interface web por {usuario.get_full_name() or usuario.username}',
        erro='\n'.join(erros) if erros else '',
        executado_por=f'web:{usuario.username}'
    )
    
    return {
        'criadas': criadas,
        'duplicadas': duplicadas,
        'erros': erros,
        'comandas_criadas': comandas_criadas,
        'mes_referencia': mes_referencia,
    }


@staff_member_required
def preview_comandas_view(request):
    """
    Preview das comandas que serão geradas (sem criar no banco).
    """
    
    mes_selecionado = request.GET.get('mes')
    
    if not mes_selecionado:
        return redirect('gerar_comandas')
    
    try:
        mes_referencia = datetime.strptime(mes_selecionado, '%Y-%m').date()
    except ValueError:
        messages.error(request, '❌ Formato de data inválido!')
        return redirect('gerar_comandas')
    
    # Buscar locações ativas
    locacoes_ativas = Locacao.objects.filter(
        status='ACTIVE',
        is_active=True
    ).select_related('imovel', 'locatario')
    
    config = ConfiguracaoSistema.get_config()
    dia_padrao = config.dia_vencimento_padrao
    
    # Preparar preview
    preview_comandas = []
    
    for locacao in locacoes_ativas:
        # Verificar se já existe
        ja_existe = Comanda.objects.filter(
            locacao=locacao,
            mes_referencia=mes_referencia
        ).exists()
        
        # Calcular dia de vencimento
        dia_vencimento = getattr(locacao, 'dia_vencimento', None) or dia_padrao
        ultimo_dia = calendar.monthrange(mes_referencia.year, mes_referencia.month)[1]
        if dia_vencimento > ultimo_dia:
            dia_vencimento = ultimo_dia
        
        data_vencimento = mes_referencia.replace(day=dia_vencimento)
        
        # Calcular valor total
        valor_aluguel = locacao.valor_aluguel
        valor_condominio = getattr(locacao.imovel, 'valor_condominio', Decimal('0.00')) or Decimal('0.00')
        valor_total = valor_aluguel + valor_condominio
        
        preview_comandas.append({
            'locacao': locacao,
            'valor_aluguel': valor_aluguel,
            'valor_condominio': valor_condominio,
            'valor_total': valor_total,
            'data_vencimento': data_vencimento,
            'ja_existe': ja_existe,
        })
    
    context = {
        'mes_referencia': mes_referencia,
        'mes_label': mes_referencia.strftime('%B/%Y').capitalize(),
        'preview_comandas': preview_comandas,
        'total_comandas': len(preview_comandas),
        'total_novas': sum(1 for c in preview_comandas if not c['ja_existe']),
        'total_existentes': sum(1 for c in preview_comandas if c['ja_existe']),
    }
    
    return render(request, 'core/preview_comandas.html', context)
