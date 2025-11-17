#!/bin/bash

# ═══════════════════════════════════════════════════════════
# ETAPA 3: ENVIO DE COMANDAS VIA WHATSAPP/EMAIL
# ═══════════════════════════════════════════════════════════

echo "════════════════════════════════════════════════════════"
echo "🎯 ETAPA 3: Implementando Envio de Comandas"
echo "════════════════════════════════════════════════════════"
echo ""

# Fazer backups
echo "📦 Criando backups..."
cp ~/sgli_system/core/admin.py ~/sgli_system/core/admin.py.backup_etapa3_$(date +%Y%m%d_%H%M%S)
cp ~/sgli_system/core/views.py ~/sgli_system/core/views.py.backup_etapa3_$(date +%Y%m%d_%H%M%S)
cp ~/sgli_system/core/urls.py ~/sgli_system/core/urls.py.backup_etapa3_$(date +%Y%m%d_%H%M%S)

echo ""
echo "✏️  PASSO 1: Adicionando views de comanda..."

# ═══════════════════════════════════════════════════════════
# ADICIONAR VIEWS
# ═══════════════════════════════════════════════════════════

cat >> ~/sgli_system/core/views.py << 'VIEW_EOF'


# ═══════════════════════════════════════════════════════════
# VIEWS DE COMANDA - ENVIO WHATSAPP/EMAIL
# ═══════════════════════════════════════════════════════════

@staff_member_required
def comanda_web_view(request, comanda_id):
    """Página web bonita da comanda para visualização/compartilhamento"""
    from django.shortcuts import render, get_object_or_404
    from .models import Comanda
    from django.utils import timezone
    
    comanda = get_object_or_404(Comanda, id=comanda_id)
    locacao = comanda.locacao
    locatario = locacao.locatario
    imovel = locacao.imovel
    
    # Calcular dias de atraso
    hoje = timezone.now().date()
    dias_atraso = (hoje - comanda.data_vencimento).days if hoje > comanda.data_vencimento else 0
    
    context = {
        'titulo': f'Comanda {comanda.numero_comanda}',
        'comanda': comanda,
        'locacao': locacao,
        'locatario_nome': locatario.nome_razao_social,
        'imovel_endereco': f'{imovel.endereco}, {imovel.numero} - {imovel.bairro}',
        'numero_comanda': comanda.numero_comanda,
        'data_vencimento': comanda.data_vencimento.strftime('%d/%m/%Y'),
        'valor_aluguel': f'{comanda.valor_aluguel:,.2f}',
        'valor_condominio': f'{comanda.valor_condominio:,.2f}',
        'valor_iptu': f'{comanda.valor_iptu:,.2f}',
        'valor_multa': f'{comanda.multa:,.2f}',
        'valor_juros': f'{comanda.juros:,.2f}',
        'valor_total': f'{comanda.valor_total:,.2f}',
        'tem_multa_juros': (comanda.multa > 0 or comanda.juros > 0),
        'dias_atraso': dias_atraso,
        'mensagem': f'Segue comanda de cobrança referente ao imóvel {imovel.endereco}, {imovel.numero}.',
    }
    
    return render(request, 'admin/comanda_web.html', context)


@staff_member_required
def enviar_comanda_email(request, comanda_id):
    """Envia comanda por email"""
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from django.core.mail import EmailMessage
    from django.conf import settings
    from .models import Comanda
    
    comanda = get_object_or_404(Comanda, id=comanda_id)
    locatario = comanda.locacao.locatario
    
    if not locatario.email:
        messages.error(request, f'❌ Locatário {locatario.nome_razao_social} não possui email cadastrado!')
        return redirect('admin:core_comanda_changelist')
    
    try:
        # URL da comanda web
        comanda_url = request.build_absolute_uri(f'/comanda/{comanda.id}/web/')
        
        # Montar email
        assunto = f'Comanda {comanda.numero_comanda} - HABITAT PRO'
        
        corpo = f'''Prezado(a) {locatario.nome_razao_social},

Segue comanda de cobrança referente ao imóvel {comanda.locacao.imovel.endereco}, {comanda.locacao.imovel.numero}.

📋 Número da Comanda: {comanda.numero_comanda}
📅 Vencimento: {comanda.data_vencimento.strftime('%d/%m/%Y')}
💰 Valor Total: R$ {comanda.valor_total:,.2f}

🔗 Visualizar comanda completa:
{comanda_url}

Atenciosamente,
HABITAT PRO
Sistema de Gestão Imobiliária
'''
        
        email = EmailMessage(
            subject=assunto,
            body=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[locatario.email],
        )
        
        email.send()
        
        messages.success(request, f'📧 Comanda enviada com sucesso para {locatario.email}!')
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Erro ao enviar comanda por email: {e}')
        messages.error(request, f'❌ Erro ao enviar email: {str(e)}')
    
    return redirect('admin:core_comanda_changelist')
VIEW_EOF

echo "✅ Views adicionadas ao views.py"

echo ""
echo "✏️  PASSO 2: Adicionando URLs..."

# ═══════════════════════════════════════════════════════════
# ADICIONAR URLS
# ═══════════════════════════════════════════════════════════

# Verificar se as URLs já existem
if grep -q "comanda_web_view" ~/sgli_system/core/urls.py; then
    echo "⚠️  URLs de comanda já existem. Pulando..."
else
    # Importar views se ainda não estiver
    if ! grep -q "comanda_web_view" ~/sgli_system/core/urls.py; then
        sed -i '/from \.views import (/a\    comanda_web_view,\n    enviar_comanda_email,' ~/sgli_system/core/urls.py
    fi
    
    # Adicionar URLs antes do último ]
    sed -i '/^]$/i\    \n    # Comandas\n    path("comanda/<uuid:comanda_id>/web/", \n         comanda_web_view, \n         name="comanda_web_view"),\n    \n    path("comanda/<uuid:comanda_id>/enviar-email/", \n         enviar_comanda_email, \n         name="enviar_comanda_email"),' ~/sgli_system/core/urls.py
fi

echo "✅ URLs adicionadas ao urls.py"

echo ""
echo "✏️  PASSO 3: Adicionando botões de envio ao ComandaAdmin..."

# ═══════════════════════════════════════════════════════════
# ADICIONAR COLUNA DE AÇÕES NO COMANDAADMIN
# ═══════════════════════════════════════════════════════════

cat > /tmp/add_acoes_comanda.py << 'PYTHON_EOF'
#!/usr/bin/env python3
import sys

# Ler admin.py
with open('/home/claude/sgli_system/core/admin.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar ComandaAdmin
comanda_admin_line = None
for i, line in enumerate(lines):
    if 'class ComandaAdmin(admin.ModelAdmin)' in line:
        comanda_admin_line = i
        break

if comanda_admin_line is None:
    print("❌ ComandaAdmin não encontrado!")
    sys.exit(1)

# Verificar se acoes_envio já existe
already_exists = False
for i in range(comanda_admin_line, min(comanda_admin_line + 300, len(lines))):
    if 'def acoes_envio' in lines[i]:
        already_exists = True
        break

if already_exists:
    print("✅ Ações de envio já existem! Nada a fazer.")
    sys.exit(0)

# Encontrar list_display em ComandaAdmin
list_display_line = None
for i in range(comanda_admin_line, min(comanda_admin_line + 80, len(lines))):
    if 'list_display' in lines[i] and '=' in lines[i]:
        list_display_line = i
        break

if list_display_line is None:
    print("❌ list_display não encontrado em ComandaAdmin!")
    sys.exit(1)

# Encontrar fechamento do list_display
list_display_end = list_display_line
bracket_count = 0
started = False
for i in range(list_display_line, min(list_display_line + 30, len(lines))):
    line = lines[i]
    if '[' in line:
        started = True
        bracket_count += line.count('[')
    if started:
        bracket_count -= line.count(']')
        if bracket_count == 0:
            list_display_end = i
            break

# Adicionar 'acoes_envio' ao list_display
if ']' in lines[list_display_end]:
    full_list_display = ''.join(lines[list_display_line:list_display_end+1])
    if 'acoes_envio' not in full_list_display:
        lines[list_display_end] = lines[list_display_end].replace(']', "        'acoes_envio',\n    ]")

# Encontrar onde inserir o método (após dias_vencimento ou outro método)
insert_line = None
for i in range(list_display_end, min(comanda_admin_line + 400, len(lines))):
    if 'def dias_vencimento' in lines[i]:
        # Procurar fim deste método
        for j in range(i, min(i + 30, len(lines))):
            if lines[j].strip().startswith('def ') and j > i:
                insert_line = j
                break
        if insert_line:
            break

if insert_line is None:
    # Procurar último método display
    for i in range(comanda_admin_line, min(comanda_admin_line + 400, len(lines))):
        if '@admin.display' in lines[i]:
            last_display = i

    # Ir até próximo def após último display
    for i in range(last_display, min(last_display + 50, len(lines))):
        if lines[i].strip().startswith('def ') and 'display' not in lines[i-1]:
            insert_line = i
            break

if insert_line is None:
    insert_line = list_display_end + 50

# Adicionar método acoes_envio
new_method = '''
    @admin.display(description='📤 Ações')
    def acoes_envio(self, obj):
        """Botões para enviar comanda via WhatsApp e Email"""
        from django.utils.html import format_html
        from django.urls import reverse
        import urllib.parse
        
        locatario = obj.locacao.locatario
        
        # URL da comanda web
        comanda_url = f'/comanda/{obj.id}/web/'
        
        # Botão WhatsApp
        telefone = locatario.telefone if locatario.telefone else ''
        telefone_limpo = ''.join(filter(str.isdigit, telefone))
        
        if not telefone_limpo.startswith('55'):
            telefone_limpo = '55' + telefone_limpo
        
        # Mensagem WhatsApp
        mensagem = f'''Olá {locatario.nome_razao_social}!

📋 Comanda: {obj.numero_comanda}
📅 Vencimento: {obj.data_vencimento.strftime('%d/%m/%Y')}
💰 Valor: R$ {obj.valor_total:,.2f}

🔗 Ver detalhes completos:
{self.admin_site.site_url}{comanda_url}

HABITAT PRO'''
        
        mensagem_encoded = urllib.parse.quote(mensagem)
        whatsapp_url = f'https://wa.me/{telefone_limpo}?text={mensagem_encoded}'
        
        # URL para enviar email
        email_url = reverse('enviar_comanda_email', kwargs={'comanda_id': obj.id})
        
        # Botões HTML
        botoes = f'''
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <a href="{whatsapp_url}" target="_blank" 
               style="display: inline-block; background: #25D366; color: white; 
                      padding: 6px 12px; border-radius: 6px; text-decoration: none; 
                      font-weight: bold; font-size: 11px; white-space: nowrap;
                      box-shadow: 0 2px 6px rgba(37, 211, 102, 0.3);"
               title="Enviar via WhatsApp">
                💬 WhatsApp
            </a>
            <a href="{email_url}" 
               style="display: inline-block; background: #3b82f6; color: white; 
                      padding: 6px 12px; border-radius: 6px; text-decoration: none; 
                      font-weight: bold; font-size: 11px; white-space: nowrap;
                      box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);"
               title="Enviar via Email">
                📧 Email
            </a>
            <a href="{comanda_url}" target="_blank"
               style="display: inline-block; background: #8b5cf6; color: white; 
                      padding: 6px 12px; border-radius: 6px; text-decoration: none; 
                      font-weight: bold; font-size: 11px; white-space: nowrap;
                      box-shadow: 0 2px 6px rgba(139, 92, 246, 0.3);"
               title="Visualizar comanda">
                👁️ Ver
            </a>
        </div>
        '''
        
        return format_html(botoes)
    
'''

lines.insert(insert_line, new_method)

# Salvar
with open('/home/claude/sgli_system/core/admin.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Método acoes_envio adicionado com sucesso!")
print(f"   Inserido na linha {insert_line}")
PYTHON_EOF

chmod +x /tmp/add_acoes_comanda.py
python3 /tmp/add_acoes_comanda.py

if [ $? -eq 0 ]; then
    echo "✅ Botões de ação adicionados ao ComandaAdmin"
    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "✅ ETAPA 3 CONCLUÍDA COM SUCESSO!"
    echo "════════════════════════════════════════════════════════"
    echo ""
    echo "📋 Modificações aplicadas:"
    echo "   • Views: comanda_web_view() + enviar_comanda_email()"
    echo "   • URLs: /comanda/<id>/web/ + /enviar-email/"
    echo "   • ComandaAdmin: coluna 'acoes_envio' com 3 botões:"
    echo "     💬 WhatsApp - Abre wa.me automaticamente"
    echo "     📧 Email - Envia email com link da comanda"
    echo "     👁️  Ver - Abre página bonita da comanda"
    echo "   • Template comanda_web.html já existe ✅"
    echo ""
else
    echo ""
    echo "❌ ERRO na aplicação. Restaurando backups..."
    cp ~/sgli_system/core/admin.py.backup_etapa3_* ~/sgli_system/core/admin.py
    cp ~/sgli_system/core/views.py.backup_etapa3_* ~/sgli_system/core/views.py
    cp ~/sgli_system/core/urls.py.backup_etapa3_* ~/sgli_system/core/urls.py
    exit 1
fi
