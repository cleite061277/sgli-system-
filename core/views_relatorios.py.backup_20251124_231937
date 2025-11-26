from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta, datetime
from decimal import Decimal
from core.models import Comanda, Locacao, Imovel, Pagamento
import json

# ========== FUNÇÕES ORIGINAIS (PRESERVADAS) ==========

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


# ========== NOVAS FUNÇÕES - DASHBOARD FINANCEIRO ==========

@staff_member_required
def dashboard_financeiro(request):
    """
    Dashboard Financeiro completo com KPIs, gráficos e tabelas.
    Template: core/templates/relatorios/dashboard_financeiro.html
    """
    hoje = timezone.now().date()
    
    # Parâmetros de filtro (opcional)
    periodo = request.GET.get('periodo', 'mes')  # mes, trimestre, semestre, ano
    imovel_id = request.GET.get('imovel')
    status_filter = request.GET.get('status')
    
    # Calcular data inicial baseada no período
    if periodo == 'trimestre':
        data_inicio = hoje - timedelta(days=90)
    elif periodo == 'semestre':
        data_inicio = hoje - timedelta(days=180)
    elif periodo == 'ano':
        data_inicio = hoje - timedelta(days=365)
    else:  # mes
        data_inicio = hoje.replace(day=1)
    
    # Query base
    comandas_query = Comanda.objects.filter(
        mes_referencia__gte=data_inicio,
        is_active=True
    )
    
    # Aplicar filtros opcionais
    if imovel_id:
        comandas_query = comandas_query.filter(locacao__imovel_id=imovel_id)
    
    if status_filter:
        if status_filter == 'pago':
            comandas_query = comandas_query.filter(status='PAID')
        elif status_filter == 'pendente':
            comandas_query = comandas_query.filter(status='PENDING')
        elif status_filter == 'atrasado':
            comandas_query = comandas_query.filter(status='OVERDUE')
    
    # KPIs Principais
    receita_prevista = comandas_query.aggregate(
        total=Sum('_valor_aluguel_historico')
    )['total'] or Decimal('0.00')
    
    receita_realizada = comandas_query.filter(status='PAID').aggregate(
        total=Sum('valor_pago')
    )['total'] or Decimal('0.00')
    
    comandas_atrasadas = comandas_query.filter(
        status='OVERDUE',
        data_vencimento__lt=hoje
    )
    
    valor_inadimplencia = comandas_atrasadas.aggregate(
        total=Sum('_valor_aluguel_historico')
    )['total'] or Decimal('0.00')
    
    taxa_inadimplencia = (
        float(valor_inadimplencia) / float(receita_prevista) * 100
    ) if receita_prevista > 0 else 0
    
    # Taxa de ocupação
    total_imoveis = Imovel.objects.filter(is_active=True).count()
    imoveis_ocupados = Locacao.objects.filter(
        status='ACTIVE',
        is_active=True
    ).values('imovel').distinct().count()
    
    taxa_ocupacao = (
        imoveis_ocupados / total_imoveis * 100
    ) if total_imoveis > 0 else 0
    
    # Dados para gráficos - Últimos 6 meses
    meses_dados = []
    for i in range(5, -1, -1):
        mes = hoje - timedelta(days=30 * i)
        mes_ref = mes.replace(day=1)
        
        comandas_mes = Comanda.objects.filter(
            mes_referencia=mes_ref,
            is_active=True
        )
        
        previsto = comandas_mes.aggregate(
            total=Sum('_valor_aluguel_historico')
        )['total'] or Decimal('0.00')
        
        realizado = comandas_mes.filter(status='PAID').aggregate(
            total=Sum('valor_pago')
        )['total'] or Decimal('0.00')
        
        atrasadas_mes = comandas_mes.filter(status='OVERDUE').count()
        total_mes = comandas_mes.count()
        taxa_inad_mes = (atrasadas_mes / total_mes * 100) if total_mes > 0 else 0
        
        meses_dados.append({
            'mes': mes_ref.strftime('%b/%y'),
            'previsto': float(previsto),
            'realizado': float(realizado),
            'inadimplencia': round(taxa_inad_mes, 1)
        })
    
    # Performance por imóvel (Top 5)
    imoveis_performance = []
    imoveis = Imovel.objects.filter(is_active=True)[:5]
    
    for imovel in imoveis:
        comandas_imovel = Comanda.objects.filter(
            locacao__imovel=imovel,
            mes_referencia__gte=data_inicio,
            is_active=True
        )
        
        previsto = comandas_imovel.aggregate(
            total=Sum('_valor_aluguel_historico')
        )['total'] or Decimal('0.00')
        
        realizado = comandas_imovel.filter(status='PAID').aggregate(
            total=Sum('valor_pago')
        )['total'] or Decimal('0.00')
        
        imoveis_performance.append({
            'nome': f"{imovel.tipo} - {imovel.endereco[:30]}",
            'previsto': float(previsto),
            'realizado': float(realizado)
        })
    
    # Comandas pendentes (para tabela)
    comandas_pendentes = comandas_query.filter(
        status='PENDING'
    ).select_related(
        'locacao',
        'locacao__imovel',
        'locacao__locatario'
    ).order_by('data_vencimento')[:10]
    
    # Comandas atrasadas (para tabela)
    comandas_atrasadas_lista = comandas_atrasadas.select_related(
        'locacao',
        'locacao__imovel',
        'locacao__locatario'
    ).order_by('data_vencimento')[:10]
    
    # Lista de imóveis para filtro
    todos_imoveis = Imovel.objects.filter(is_active=True).order_by('endereco')
    
    context = {
        # KPIs
        'receita_prevista': receita_prevista,
        'receita_realizada': receita_realizada,
        'taxa_realizacao': round(
            float(receita_realizada) / float(receita_prevista) * 100, 1
        ) if receita_prevista > 0 else 0,
        'valor_inadimplencia': valor_inadimplencia,
        'taxa_inadimplencia': round(taxa_inadimplencia, 1),
        'taxa_ocupacao': round(taxa_ocupacao, 1),
        'total_imoveis': total_imoveis,
        'imoveis_ocupados': imoveis_ocupados,
        
        # Dados para gráficos (JSON)
        'meses_dados_json': json.dumps(meses_dados),
        'imoveis_performance_json': json.dumps(imoveis_performance),
        
        # Tabelas
        'comandas_pendentes': comandas_pendentes,
        'comandas_atrasadas': comandas_atrasadas_lista,
        
        # Filtros
        'periodo': periodo,
        'imovel_id': imovel_id,
        'status_filter': status_filter,
        'todos_imoveis': todos_imoveis,
        
        # Data
        'hoje': hoje,
        'data_inicio': data_inicio,
    }
    
    return render(request, 'relatorios/dashboard_financeiro.html', context)


@staff_member_required
def exportar_dashboard_excel(request):
    """
    Exporta dados do dashboard para Excel (XLSX).
    Requer: openpyxl
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        return HttpResponse(
            "Biblioteca openpyxl não instalada. Execute: pip install openpyxl",
            status=500
        )
    
    hoje = timezone.now().date()
    
    # Criar workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Dashboard Financeiro"
    
    # Estilos
    header_fill = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    # Cabeçalho
    ws['A1'] = "DASHBOARD FINANCEIRO - HABITAT PRO"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'] = f"Gerado em: {hoje.strftime('%d/%m/%Y')}"
    
    # KPIs
    ws['A4'] = "INDICADORES PRINCIPAIS"
    ws['A4'].font = Font(bold=True)
    
    comandas = Comanda.objects.filter(is_active=True)
    receita_prevista = comandas.aggregate(
        total=Sum('_valor_aluguel_historico')
    )['total'] or Decimal('0.00')
    
    receita_realizada = comandas.filter(status='PAID').aggregate(
        total=Sum('valor_pago')
    )['total'] or Decimal('0.00')
    
    ws['A5'] = "Receita Prevista"
    ws['B5'] = float(receita_prevista)
    ws['B5'].number_format = 'R$ #,##0.00'
    
    ws['A6'] = "Receita Realizada"
    ws['B6'] = float(receita_realizada)
    ws['B6'].number_format = 'R$ #,##0.00'
    
    ws['A7'] = "Taxa de Realização"
    ws['B7'] = f"{float(receita_realizada) / float(receita_prevista) * 100:.1f}%" if receita_prevista > 0 else "0%"
    
    # Comandas
    ws['A9'] = "COMANDAS"
    ws['A9'].font = Font(bold=True)
    
    headers = ['Imóvel', 'Locatário', 'Vencimento', 'Valor', 'Status']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=10, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
    
    comandas_lista = comandas.select_related(
        'locacao', 'locacao__imovel', 'locacao__locatario'
    ).order_by('-data_vencimento')[:50]
    
    for row, comanda in enumerate(comandas_lista, start=11):
        ws.cell(row=row, column=1, value=str(comanda.locacao.imovel))
        ws.cell(row=row, column=2, value=comanda.locacao.locatario.nome)
        ws.cell(row=row, column=3, value=comanda.data_vencimento.strftime('%d/%m/%Y'))
        
        cell = ws.cell(row=row, column=4, value=float(comanda.valor_aluguel))
        cell.number_format = 'R$ #,##0.00'
        
        ws.cell(row=row, column=5, value=comanda.get_status_display())
    
    # Ajustar largura das colunas
    for col in range(1, 6):
        ws.column_dimensions[get_column_letter(col)].width = 20
    
    # Preparar resposta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="dashboard_financeiro_{hoje.strftime("%Y%m%d")}.xlsx"'
    
    wb.save(response)
    return response


@staff_member_required
def exportar_dashboard_pdf(request):
    """
    Exporta dashboard para PDF.
    Requer: weasyprint
    """
    try:
        from weasyprint import HTML
    except ImportError:
        return HttpResponse(
            "Biblioteca weasyprint não instalada. Execute: pip install weasyprint",
            status=500
        )
    
    # Renderizar template
    hoje = timezone.now().date()
    
    comandas = Comanda.objects.filter(is_active=True)
    receita_prevista = comandas.aggregate(
        total=Sum('_valor_aluguel_historico')
    )['total'] or Decimal('0.00')
    
    receita_realizada = comandas.filter(status='PAID').aggregate(
        total=Sum('valor_pago')
    )['total'] or Decimal('0.00')
    
    context = {
        'hoje': hoje,
        'receita_prevista': receita_prevista,
        'receita_realizada': receita_realizada,
        'comandas': comandas.select_related(
            'locacao', 'locacao__imovel', 'locacao__locatario'
        ).order_by('-data_vencimento')[:30],
    }
    
    # HTML simples para PDF
    html_string = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial; margin: 40px; }}
            h1 {{ color: #667eea; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: #667eea; color: white; padding: 10px; text-align: left; }}
            td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <h1>Dashboard Financeiro - HABITAT PRO</h1>
        <p><strong>Gerado em:</strong> {hoje.strftime('%d/%m/%Y')}</p>
        
        <h2>Indicadores</h2>
        <p><strong>Receita Prevista:</strong> R$ {receita_prevista:,.2f}</p>
        <p><strong>Receita Realizada:</strong> R$ {receita_realizada:,.2f}</p>
        
        <h2>Comandas Recentes</h2>
        <table>
            <tr>
                <th>Imóvel</th>
                <th>Locatário</th>
                <th>Vencimento</th>
                <th>Valor</th>
                <th>Status</th>
            </tr>
    """
    
    for comanda in context['comandas']:
        html_string += f"""
            <tr>
                <td>{comanda.locacao.imovel}</td>
                <td>{comanda.locacao.locatario.nome}</td>
                <td>{comanda.data_vencimento.strftime('%d/%m/%Y')}</td>
                <td>R$ {comanda.valor_aluguel:,.2f}</td>
                <td>{comanda.get_status_display()}</td>
            </tr>
        """
    
    html_string += """
        </table>
    </body>
    </html>
    """
    
    # Gerar PDF
    pdf = HTML(string=html_string).write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="dashboard_financeiro_{hoje.strftime("%Y%m%d")}.pdf"'
    
    return response


@staff_member_required
def enviar_relatorio_email(request):
    """
    Envia relatório por email via SendGrid.
    Requer POST com 'destinatario'
    """
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=405)
    
    destinatario = request.POST.get('destinatario')
    if not destinatario:
        return JsonResponse({'erro': 'Destinatário não informado'}, status=400)
    
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        hoje = timezone.now().date()
        
        # Coletar dados
        comandas = Comanda.objects.filter(is_active=True)
        receita_prevista = comandas.aggregate(
            total=Sum('_valor_aluguel_historico')
        )['total'] or Decimal('0.00')
        
        receita_realizada = comandas.filter(status='PAID').aggregate(
            total=Sum('valor_pago')
        )['total'] or Decimal('0.00')
        
        # Montar email
        assunto = f"Dashboard Financeiro - {hoje.strftime('%d/%m/%Y')}"
        
        mensagem = f"""
Dashboard Financeiro - HABITAT PRO
Gerado em: {hoje.strftime('%d/%m/%Y')}

INDICADORES PRINCIPAIS:
- Receita Prevista: R$ {receita_prevista:,.2f}
- Receita Realizada: R$ {receita_realizada:,.2f}
- Taxa de Realização: {float(receita_realizada) / float(receita_prevista) * 100:.1f}%

Para ver o relatório completo, acesse:
{request.build_absolute_uri('/relatorios/dashboard/')}

--
HABITAT PRO
Sistema de Gestão de Locação de Imóveis
        """
        
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [destinatario],
            fail_silently=False,
        )
        
        return JsonResponse({
            'sucesso': True,
            'mensagem': f'Relatório enviado para {destinatario}'
        })
        
    except Exception as e:
        return JsonResponse({
            'erro': f'Erro ao enviar email: {str(e)}'
        }, status=500)
