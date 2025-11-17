from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from datetime import datetime

# Imports básicos que sabemos que funcionam
from .models import Usuario, Locador, Imovel, Locatario, Locacao, Comanda, Pagamento
from .serializers import (
    UsuarioSerializer, LocadorSerializer, ImovelSerializer,
    LocatarioSerializer, LocacaoSerializer, ComandaSerializer, PagamentoSerializer
)

# ViewSets básicos que funcionavam antes
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

class LocadorViewSet(viewsets.ModelViewSet):
    queryset = Locador.objects.all()
    serializer_class = LocadorSerializer
    permission_classes = [IsAuthenticated]

class ImovelViewSet(viewsets.ModelViewSet):
    queryset = Imovel.objects.all()
    serializer_class = ImovelSerializer
    permission_classes = [IsAuthenticated]

class LocatarioViewSet(viewsets.ModelViewSet):
    queryset = Locatario.objects.all()
    serializer_class = LocatarioSerializer
    permission_classes = [IsAuthenticated]

class LocacaoViewSet(viewsets.ModelViewSet):
    queryset = Locacao.objects.all()
    serializer_class = LocacaoSerializer
    permission_classes = [IsAuthenticated]

class ComandaViewSet(viewsets.ModelViewSet):
    queryset = Comanda.objects.all()
    serializer_class = ComandaSerializer
    permission_classes = [IsAuthenticated]



from django.http import JsonResponse
from decimal import Decimal

def teste_simples(request):
    """View de teste sem qualquer autenticação."""
    comandas = Comanda.objects.all()
    total = comandas.count()
    
    lista = []
    for c in comandas[:3]:
        lista.append({
            'numero': c.numero_comanda,
            'status': c.get_status_display()
        })
    
    return JsonResponse({
        'total': total,
        'comandas': lista,
        'funcionando': True
    })

class PagamentoViewSet(viewsets.ModelViewSet):
    """ViewSet for payment management."""
    queryset = Pagamento.objects.select_related('comanda', 'usuario_registro').all()
    serializer_class = PagamentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'forma_pagamento', 'comanda']
    search_fields = ['numero_pagamento', 'comanda__numero_comanda']
    ordering_fields = ['data_pagamento', 'valor_pago', 'created_at']
    ordering = ['-data_pagamento']
    
    def perform_create(self, serializer):
        serializer.save(usuario_registro=self.request.user)

