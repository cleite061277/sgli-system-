from django import forms
from .models import Pagamento, Comanda

class PagamentoAdminForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customizar o campo comanda para mostrar mais informações
        self.fields['comanda'].label_from_instance = self.label_from_comanda
    
    @staticmethod
    def label_from_comanda(obj):
        """Customizar como cada comanda aparece no dropdown."""
        locatario = obj.locacao.locatario.nome_razao_social
        contrato = obj.locacao.numero_contrato
        valor = f"R$ {obj.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"{obj.numero_comanda} - {locatario} - Contrato: {contrato} - Total: {valor}"
