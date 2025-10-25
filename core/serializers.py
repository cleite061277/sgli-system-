from rest_framework import serializers
from .models import Usuario, Locador, Imovel, Locatario, Locacao, Comanda, Pagamento

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'is_active']

class LocadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locador
        fields = '__all__'

class ImovelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Imovel
        fields = '__all__'

class LocatarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locatario
        fields = '__all__'

class LocacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locacao
        fields = '__all__'

class ComandaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comanda
        fields = '__all__'



class PagamentoSerializer(serializers.ModelSerializer):
    comanda_numero = serializers.CharField(source='comanda.numero_comanda', read_only=True)
    usuario_nome = serializers.CharField(source='usuario_registro.get_full_name', read_only=True)
    valor_formatado = serializers.SerializerMethodField()
    
    class Meta:
        model = Pagamento
        fields = [
            'id', 'numero_pagamento', 'comanda', 'comanda_numero',
            'valor_pago', 'valor_formatado', 'data_pagamento',
            'forma_pagamento', 'status', 'usuario_registro', 'usuario_nome',
            'comprovante', 'observacoes', 'data_confirmacao',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['numero_pagamento', 'data_confirmacao']
    
    def get_valor_formatado(self, obj):
        from .utils import formatar_moeda_brasileira
        return formatar_moeda_brasileira(obj.valor_pago)
