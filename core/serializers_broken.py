from rest_framework import serializers
from decimal import Decimal
from .models import Usuario, Locador, Imovel, Locatario, Locacao, Comanda

# Manter apenas os serializers básicos necessários
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'tipo_usuario']

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

# Adicionar Pagamento apenas se o modelo existir
try:
except NameError:
    print("Modelo Pagamento não encontrado - será adicionado depois")

