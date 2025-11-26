from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.utils import timezone
from decimal import Decimal # Importação necessária para valores monetários
from .models import Usuario, Locador, Imovel, Locatario, Locacao, Comanda
from .serializers import (
    UsuarioSerializer, LocadorSerializer, ImovelSerializer,
    LocatarioSerializer, LocacaoSerializer, ComandaSerializer
)

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tipo_usuario', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']

class LocadorViewSet(viewsets.ModelViewSet):
    queryset = Locador.objects.all()
    serializer_class = LocadorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tipo_locador', 'is_active']
    search_fields = ['nome_razao_social', 'cpf_cnpj', 'email']

class ImovelViewSet(viewsets.ModelViewSet):
    queryset = Imovel.objects.all()
    serializer_class = ImovelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tipo_imovel', 'status', 'estado', 'is_active']
    search_fields = ['codigo_imovel', 'endereco', 'bairro', 'cidade']

class LocatarioViewSet(viewsets.ModelViewSet):
    queryset = Locatario.objects.all()
    serializer_class = LocatarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['nome_razao_social', 'cpf_cnpj', 'email']

class LocacaoViewSet(viewsets.ModelViewSet):
    queryset = Locacao.objects.all()
    serializer_class = LocacaoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'is_active']
    search_fields = ['numero_contrato', 'imovel__codigo_imovel', 'locatario__nome_razao_social']

class ComandaViewSet(viewsets.ModelViewSet):
    queryset = Comanda.objects.all()
    serializer_class = ComandaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'ano_referencia', 'mes_referencia', 'is_active']
    search_fields = ['numero_comanda', 'locacao__numero_contrato', 'locacao__locatario__nome_razao_social']

    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        """Get all overdue invoices."""
        hoje = timezone.now().date()
        comandas_vencidas = self.get_queryset().filter(
            data_vencimento__lt=hoje,
            status__in=[Comanda.StatusComanda.PENDENTE, Comanda.StatusComanda.PARCIALMENTE_PAGA]
        )

        page = self.paginate_queryset(comandas_vencidas)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(comandas_vencidas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pendentes(self, request):
        """Get all pending invoices."""
        comandas_pendentes = self.get_queryset().filter(
            status=Comanda.StatusComanda.PENDENTE
        )

        page = self.paginate_queryset(comandas_pendentes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(comandas_pendentes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def registrar_pagamento(self, request, pk=None):
        """Register payment for an invoice."""
        comanda = self.get_object()

        valor_pago = request.data.get('valor_pago')
        data_pagamento = request.data.get('data_pagamento')
        forma_pagamento = request.data.get('forma_pagamento', '')

        if not valor_pago:
            return Response(
                {'error': 'valor_pago is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Converte para Decimal ao invés de float para precisão monetária
            valor_pago = Decimal(valor_pago)
            if valor_pago <= 0:
                return Response(
                    {'error': 'valor_pago must be greater than 0.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid valor_pago format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update payment information
        comanda.valor_pago += valor_pago
        if data_pagamento:
            comanda.data_pagamento = data_pagamento
        else:
            comanda.data_pagamento = timezone.now().date()

        comanda.forma_pagamento = forma_pagamento

        # Handle uploaded receipt
        if 'comprovante_pagamento' in request.FILES:
            comanda.comprovante_pagamento = request.FILES['comprovante_pagamento']

        comanda.save() # This will auto-update status via model save method

        serializer = self.get_serializer(comanda)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get financial dashboard data."""
        hoje = timezone.now().date()
        mes_atual = hoje.month
        ano_atual = hoje.year

        queryset = self.get_queryset()

        # Calculate dashboard metrics
        # CORREÇÃO: Usando Decimal('0.00')
        total_pendente = queryset.filter(
            status__in=[Comanda.StatusComanda.PENDENTE, Comanda.StatusComanda.PARCIALMENTE_PAGA]
        ).aggregate(total=Sum('valor_aluguel'))['total'] or Decimal('0.00')

        total_vencidas = queryset.filter(
            data_vencimento__lt=hoje,
            status__in=[Comanda.StatusComanda.PENDENTE, Comanda.StatusComanda.PARCIALMENTE_PAGA]
        ).count()

        # CORREÇÃO: Usando Decimal('0.00')
        total_mes_atual = queryset.filter(
            mes_referencia=mes_atual,
            ano_referencia=ano_atual
        ).aggregate(total=Sum('valor_aluguel'))['total'] or Decimal('0.00')

        # CORREÇÃO: Usando Decimal('0.00')
        total_pago_mes = queryset.filter(
            mes_referencia=mes_atual,
            ano_referencia=ano_atual,
            status=Comanda.StatusComanda.PAGA
        ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
        
        # Calcular percentual de recebimento com segurança
        percentual_recebimento = (total_pago_mes / total_mes_atual * 100) if total_mes_atual > Decimal('0.00') else Decimal('0.00')
        
        return Response({
            'total_pendente': total_pendente,
            'total_vencidas': total_vencidas,
            'total_mes_atual': total_mes_atual,
            'total_pago_mes': total_pago_mes,
            'percentual_recebimento': percentual_recebimento,
            'comandas_pendentes': queryset.filter(status=Comanda.StatusComanda.PENDENTE).count(),
            'comandas_vencidas': total_vencidas,
        })

def dashboard_view(request):
    """Dashboard with system statistics."""
    hoje = timezone.now().date()

    stats = {
        'total_imoveis': Imovel.objects.filter(is_active=True).count(),
        'imoveis_disponivel': Imovel.objects.filter(status='AVAILABLE', is_active=True).count(),
        'total_locacoes': Locacao.objects.filter(status='ACTIVE', is_active=True).count(),
        'total_locadores': Locador.objects.filter(is_active=True).count(),
        'total_locatarios': Locatario.objects.filter(is_active=True).count(),
        'total_comandas': Comanda.objects.filter(is_active=True).count(),
        'comandas_pendentes': Comanda.objects.filter(status=Comanda.StatusComanda.PENDENTE, is_active=True).count(),
        'comandas_vencidas': Comanda.objects.filter(
            data_vencimento__lt=hoje,
            status__in=[Comanda.StatusComanda.PENDENTE, Comanda.StatusComanda.PARCIALMENTE_PAGA],
            is_active=True
        ).count(),
        # CORREÇÃO: Usando Decimal('0.00') e chave de agregação
        'valor_total_pendente': Comanda.objects.filter(
            status__in=[Comanda.StatusComanda.PENDENTE, Comanda.StatusComanda.PARCIALMENTE_PAGA],
            is_active=True
        ).aggregate(sum=Sum('valor_aluguel'))['sum'] or Decimal('0.00'),
    }
    return render(request, 'core/dashboard.html', stats)

def financeiro_view(request):
    """Financial dashboard view."""
    hoje = timezone.now().date()
    mes_atual = hoje.month
    ano_atual = hoje.year

    # Estatísticas financeiras
    comandas_pendentes = Comanda.objects.filter(
        status__in=[Comanda.StatusComanda.PENDENTE, Comanda.StatusComanda.PARCIALMENTE_PAGA],
        is_active=True
    )

    comandas_vencidas = Comanda.objects.filter(
        data_vencimento__lt=hoje,
        status__in=[Comanda.StatusComanda.PENDENTE, Comanda.StatusComanda.PARCIALMENTE_PAGA],
        is_active=True
    )

    comandas_mes_atual = Comanda.objects.filter(
        mes_referencia=mes_atual,
        ano_referencia=ano_atual,
        is_active=True
    )

    # CORREÇÃO: Usando Decimal('0.00') para garantir o tipo de dado correto
    stats = {
        'total_pendente': comandas_pendentes.aggregate(sum=Sum('valor_aluguel'))['sum'] or Decimal('0.00'),
        'total_vencidas': comandas_vencidas.count(),
        'valor_vencido': comandas_vencidas.aggregate(sum=Sum('valor_aluguel'))['sum'] or Decimal('0.00'),
        'comandas_mes': comandas_mes_atual.count(),
        'valor_mes': comandas_mes_atual.aggregate(sum=Sum('valor_aluguel'))['sum'] or Decimal('0.00'),
        'valor_pago_mes': comandas_mes_atual.filter(status=Comanda.StatusComanda.PAGA).aggregate(sum=Sum('valor_pago'))['sum'] or Decimal('0.00'),
        'comandas_pendentes_list': comandas_pendentes[:10], # Top 10
        'comandas_vencidas_list': comandas_vencidas[:10], # Top 10
    }

    # Calcular percentual de recebimento
    if stats['valor_mes'] > Decimal('0.00'):
        stats['percentual_recebimento'] = (stats['valor_pago_mes'] / stats['valor_mes']) * 100
    else:
        stats['percentual_recebimento'] = Decimal('0.00')

    return render(request, 'core/financeiro.html', stats)
# ============================================================================
# PAGAMENTO VIEWSETS
# ============================================================================

class PagamentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for payment management with RBAC permissions.
    """
    queryset = Pagamento.objects.select_related(
        'comanda', 'comanda__locacao', 'comanda__locacao__locatario',
        'usuario_responsavel', 'usuario_confirmacao'
    ).all()
    permission_classes = [IsAuthenticated, PagamentoPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'forma_pagamento', 'comanda__status']
    search_fields = ['numero_pagamento', 'comanda__numero_comanda', 'observacoes']
    ordering_fields = ['data_pagamento', 'valor_pago', 'created_at']
    ordering = ['-data_pagamento']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PagamentoCreateSerializer
        return PagamentoSerializer

    def perform_create(self, serializer):
        """Set responsible user on creation."""
        serializer.save(usuario_responsavel=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def confirmar(self, request, pk=None):
        """Confirm payment."""
        pagamento = self.get_object()
        
        if pagamento.status != Pagamento.StatusPagamento.PENDENTE:
            return Response(
                {'error': 'Apenas pagamentos pendentes podem ser confirmados'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pagamento.status = Pagamento.StatusPagamento.CONFIRMADO
        pagamento.usuario_confirmacao = request.user
        pagamento.save()
        
        return Response({
            'message': 'Pagamento confirmado com sucesso',
            'pagamento': PagamentoSerializer(pagamento).data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancelar(self, request, pk=None):
        """Cancel payment."""
        pagamento = self.get_object()
        motivo = request.data.get('motivo', '')
        
        if pagamento.status == Pagamento.StatusPagamento.CONFIRMADO:
            return Response(
                {'error': 'Pagamentos confirmados não podem ser cancelados diretamente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pagamento.status = Pagamento.StatusPagamento.CANCELADO
        if motivo:
            pagamento.observacoes += f"\nMotivo do cancelamento: {motivo}"
        pagamento.save()
        
        return Response({
            'message': 'Pagamento cancelado com sucesso'
        })

    @action(detail=False, methods=['get'])
    def relatorio_financeiro(self, request):
        """Generate financial report."""
        # Filtros
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        status_filter = request.query_params.get('status')
        
        queryset = self.get_queryset()
        
        if data_inicio:
            queryset = queryset.filter(data_pagamento__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_pagamento__lte=data_fim)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Agregações
        resumo = queryset.aggregate(
            total_pagamentos=models.Count('id'),
            valor_total_pago=models.Sum('valor_pago'),
            valor_confirmado=models.Sum(
                'valor_pago',
                filter=models.Q(status=Pagamento.StatusPagamento.CONFIRMADO)
            ),
            valor_pendente=models.Sum(
                'valor_pago',
                filter=models.Q(status=Pagamento.StatusPagamento.PENDENTE)
            )
        )
        
        # Formatação
        for key, value in resumo.items():
            if key.startswith('valor_') and value:
                resumo[f"{key}_formatado"] = formatar_moeda_brasileira(value)
        
        # Por forma de pagamento
        por_forma = queryset.values('forma_pagamento').annotate(
            quantidade=models.Count('id'),
            valor_total=models.Sum('valor_pago')
        ).order_by('-valor_total')
        
        return Response({
            'resumo': resumo,
            'por_forma_pagamento': por_forma,
            'periodo': {
                'data_inicio': data_inicio,
                'data_fim': data_fim
            }
        })

# ============================================================================
# RELATÓRIOS VIEWSETS
# ============================================================================

from .reports import RelatorioFinanceiro, RelatorioOperacional

class RelatoriosViewSet(viewsets.GenericViewSet):
    """
    ViewSet for reports and analytics.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def resumo_financeiro(self, request):
        """Get financial summary report."""
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
        
        relatorio = RelatorioFinanceiro(data_inicio, data_fim)
        resumo = relatorio.resumo_geral()
        
        return Response(resumo)
    
    @action(detail=False, methods=['get'])
    def evolucao_mensal(self, request):
        """Get monthly evolution report."""
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
        
        relatorio = RelatorioFinanceiro(data_inicio, data_fim)
        evolucao = relatorio.evolucao_mensal()
        
        return Response(evolucao)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard metrics."""
        relatorio = RelatorioOperacional()
        metricas = relatorio.dashboard_metricas()
        
        return Response(metricas)
    
    @action(detail=False, methods=['get'])
    def inadimplencia(self, request):
        """Get delinquency report."""
        relatorio = RelatorioFinanceiro()
        inadimplencia = relatorio.inadimplencia_detalhada()
        
        return Response(inadimplencia)
    
    @action(detail=False, methods=['get'])
    def ranking_imoveis(self, request):
        """Get property ranking report."""
        relatorio = RelatorioFinanceiro()
        ranking = relatorio.ranking_imoveis()
        
        return Response(ranking)

