from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe

class ComandaSelectWidget(forms.Select):
    """Widget customizado que mostra informações da comanda selecionada."""
    
    class Media:
        js = ('admin/js/comanda_info.js',)
    
    def render(self, name, value, attrs=None, renderer=None):
        output = super().render(name, value, attrs, renderer)
        
        # Adicionar div para mostrar informações
        info_div = '''
        <div id="comanda-info-box" style="display:none; margin-top: 10px; padding: 15px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px;">
            <p style="margin: 5px 0;"><strong>📋 Contrato:</strong> <span id="info-contrato">-</span></p>
            <p style="margin: 5px 0;"><strong>👤 Locatário:</strong> <span id="info-locatario">-</span></p>
            <p style="margin: 5px 0;"><strong>🏠 Imóvel:</strong> <span id="info-imovel">-</span></p>
            <p style="margin: 5px 0;"><strong>💰 Valor Total:</strong> <span id="info-valor">-</span></p>
        </div>
        '''
        
        return mark_safe(output + info_div)
