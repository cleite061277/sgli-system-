#!/usr/bin/env python3
"""
Correção rápida: Adiciona recibo_button ao PagamentoAdmin
"""

def fix_pagamento_admin():
    with open('core/admin.py', 'r') as f:
        lines = f.readlines()
    
    # Encontrar linha 517 (list_display do PagamentoAdmin)
    for i, line in enumerate(lines):
        if i == 516 and "list_display = ('numero_pagamento'" in line:
            # Adicionar recibo_button
            lines[i] = "    list_display = ('numero_pagamento', 'comanda', 'locatario_nome', 'valor_pago', 'data_pagamento', 'forma_pagamento', 'status', 'recibo_button')\n"
            print(f"✅ Linha {i+1} corrigida: recibo_button adicionado")
            break
    
    # Adicionar método recibo_button no PagamentoAdmin (após save_model, antes do gerar_recibo action)
    insert_pos = -1
    for i, line in enumerate(lines):
        if 'def save_model(self, request, obj, form, change):' in line and i > 500:
            # Encontrar fim do método (próximo método ou classe)
            for j in range(i+1, len(lines)):
                if lines[j].strip().startswith('def ') or lines[j].strip().startswith('@admin'):
                    insert_pos = j
                    break
            break
    
    if insert_pos > 0:
        new_method = '''
    @admin.display(description='Recibo')
    def recibo_button(self, obj):
        """Botão para visualizar/gerar recibo"""
        url = reverse('admin:visualizar_recibo_pagamento', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" onclick="window.open(this.href, \'Recibo\', \'width=800,height=600\'); return false;">🧾 Ver Recibo</a>',
            url
        )

'''
        lines.insert(insert_pos, new_method)
        print(f"✅ Método recibo_button adicionado na linha {insert_pos+1}")
    
    # Salvar
    with open('core/admin.py', 'w') as f:
        f.writelines(lines)
    
    print("\n✅ Arquivo corrigido!")
    print("\n⚠️ PRÓXIMO PASSO:")
    print("   Criar view 'visualizar_recibo_pagamento' em views.py")

if __name__ == '__main__':
    fix_pagamento_admin()
