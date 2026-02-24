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


from django.http import FileResponse, HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from .models import Pagamento
from .document_generator import DocumentGenerator
import os
import mimetypes

@staff_member_required
def download_recibo_pagamento(request, pagamento_id):
    """
    Download seguro de recibo (Word).
    POLIMÓRFICO: suporta aluguel e rescisão.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    pagamento = get_object_or_404(Pagamento, id=pagamento_id)
    
    if not request.user.has_perm('core.view_pagamento'):
        raise Http404("Permissão negada")
    
    try:
        generator = DocumentGenerator()
        
        # Guard: verificar se DocumentGenerator tem método polimórfico
        # Se não tiver, fallback para método original (só funciona para aluguel)
        if hasattr(generator, 'gerar_recibo_polimorfico'):
            filename = generator.gerar_recibo_polimorfico(pagamento)
        else:
            # Método original (só aluguel) — rescisão falhará aqui
            if not pagamento.comanda_id:
                raise Exception("Recibo de rescisão requer DocumentGenerator atualizado")
            filename = generator.gerar_recibo_pagamento(pagamento.id)
        
        file_path = os.path.join(generator.output_dir, filename)
        
        if not os.path.exists(file_path):
            raise Http404("Recibo não encontrado")
        
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            logger.info(
                f"Recibo baixado: {filename} por {request.user.username} "
                f"(Pagamento: {pagamento.numero_pagamento})"
            )
            return response
    
    except Exception as e:
        logger.error(f"Erro ao gerar recibo {pagamento_id}: {e}")
        raise Http404(f"Erro ao gerar recibo: {str(e)}")



@staff_member_required
def pagina_recibo_pagamento(request, pagamento_id):
    """
    Página dedicada para visualizar e enviar recibo de pagamento.
    """
    from django.shortcuts import render
    from django.contrib import messages
    
    # Buscar pagamento
    pagamento = get_object_or_404(Pagamento, id=pagamento_id)
    
    # Verificar permissão
    if not request.user.has_perm('core.view_pagamento'):
        raise Http404("Permissão negada")
    
    # Resolver contexto — polimórfico: aluguel (FK) ou rescisão (GenericFK)
    if pagamento.comanda_id:
        comanda   = pagamento.comanda
        locacao   = comanda.locacao   if comanda else None
        locatario = locacao.locatario if locacao else None
        imovel    = locacao.imovel    if locacao else None
        if comanda and locacao:
            ref_label = ('Comanda ' + comanda.numero_comanda
                         + ' | Vcto ' + comanda.data_vencimento.strftime('%d/%m/%Y'))
        else:
            ref_label = 'Aluguel'
    elif pagamento.content_type_id and pagamento.object_id:
        comanda   = None
        _ref      = pagamento.comanda_ref
        _rs       = _ref.rescisao if (_ref and hasattr(_ref, 'rescisao')) else None
        locacao   = _rs.locacao   if _rs else None
        locatario = locacao.locatario if locacao else None
        imovel    = locacao.imovel    if locacao else None
        if _ref and _rs:
            ref_label = ('Rescisão | Parcela ' + str(_ref.numero_parcela)
                         + ' de ' + str(_rs.quantidade_parcelas)
                         + ' | Vcto ' + _ref.data_vencimento.strftime('%d/%m/%Y'))
        else:
            ref_label = 'Rescisão'
    else:
        comanda = locacao = locatario = imovel = None
        ref_label = '—'

    # Dados para o template
    context = {
        'pagamento': pagamento,
        'comanda': comanda,
        'locacao': locacao,
        'locatario': locatario,
        'imovel': imovel,
        'ref_label': ref_label,
        'title': 'Recibo ' + pagamento.numero_pagamento,
    }
    
    # Se for requisição POST (envio de email/whatsapp)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Limpar redirect do WhatsApp se existir
        if action == 'clear_whatsapp_session':
            request.session.pop('whatsapp_redirect', None)
            return HttpResponse('OK')
        
        if action == 'email':
            try:
                from django.core.mail import EmailMessage
                from django.conf import settings
                from .document_generator import DocumentGenerator
                
                # Gerar recibo (guard para rescisão)
                generator = DocumentGenerator()
                
                # Gerar recibo (polimórfico: aluguel ou rescisão)
                if hasattr(generator, 'gerar_recibo_polimorfico'):
                    filename = generator.gerar_recibo_polimorfico(pagamento.id)
                else:
                    # Fallback para método antigo (só aluguel)
                    filename = generator.gerar_recibo_pagamento(pagamento.id)
                
                file_path = os.path.join(generator.output_dir, filename)
                
                # Preparar email
                locatario_email = locatario.email if locatario else None
                
                if not locatario_email:
                    messages.error(request, '❌ Locatário não possui email cadastrado!')
                else:
                    assunto = f'Recibo de Pagamento - {pagamento.numero_pagamento}'
                    
                    # Corpo email — polimórfico (aluguel e rescisão)
                    _nome = getattr(locatario, 'nome_razao_social', '—')
                    _end  = (imovel.endereco + ', ' + imovel.numero) if imovel else '—'
                    _sep  = '━' * 35
                    corpo = '\n'.join([
                        'Prezado(a) ' + _nome + ',',
                        '',
                        'Segue o recibo de pagamento referente ao imóvel:',
                        'Endereço: ' + _end,
                        '',
                        _sep,
                        'DETALHAMENTO DO PAGAMENTO',
                        _sep,
                        '',
                        'Recibo Nº: ' + pagamento.numero_pagamento,
                        'Data: ' + pagamento.data_pagamento.strftime('%d/%m/%Y'),
                        'Forma: ' + pagamento.get_forma_pagamento_display(),
                        'Valor Pago: R$ ' + '{:,.2f}'.format(pagamento.valor_pago),
                        '',
                        'Referente a: ' + context.get('ref_label', '—'),
                        '',
                        _sep,
                        '',
                        'Atenciosamente,',
                        'HABITAT PRO',
                        'Sistema de Gestão Imobiliária',
                    ])
                    
                    email = EmailMessage(
                        subject=assunto,
                        body=corpo,
                        from_email=settings.EMAIL_HOST_USER,
                        to=[locatario_email],
                    )
                    
                    # Anexar recibo
                    with open(file_path, 'rb') as f:
                        email.attach(filename, f.read(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                    
                    email.send()
                    
                    messages.success(request, f'📧 Email enviado com sucesso para {locatario_email}!')
                    
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Erro ao enviar email: {e}')
                import traceback
                traceback.print_exc()
                messages.error(request, f'❌ Erro ao enviar email: {str(e)}')
        
        elif action == 'whatsapp':
            try:
                import urllib.parse
                from decimal import Decimal
                
                # Telefone do locatário
                telefone = locatario.telefone if locatario else None
                
                if not telefone:
                    messages.error(request, '❌ Locatário não possui telefone cadastrado!')
                else:
                    # Limpar telefone (apenas números)
                    telefone_limpo = ''.join(filter(str.isdigit, telefone))
                    
                    # Adicionar código do país se não tiver (Brasil = 55)
                    if not telefone_limpo.startswith('55'):
                        telefone_limpo = '55' + telefone_limpo
                    
                    # Gerar URL PÚBLICA do recibo (sem senha)
                    if not pagamento.token:
                        # Gerar token se não existir
                        import uuid
                        from django.utils import timezone
                        from datetime import timedelta
                        pagamento.token = uuid.uuid4()
                        pagamento.token_expira_em = timezone.now() + timedelta(days=30)
                        pagamento.save()
                    
                    recibo_url = request.build_absolute_uri(
                        f'/recibo/{pagamento.token}/'
                    )
                    
                    # Mensagem WhatsApp — polimórfica (aluguel e rescisão)
                    _nome = getattr(locatario, 'nome_razao_social', '—')
                    _end  = (imovel.endereco + ', ' + imovel.numero) if imovel else '—'
                    _sep  = '━' * 26
                    mensagem = '\n'.join([
                        '🧾 *RECIBO DE PAGAMENTO*',
                        '',
                        'Olá *' + _nome + '*!',
                        'Confirmamos o recebimento do seu pagamento:',
                        '',
                        _sep,
                        '📋 *DADOS DO PAGAMENTO*',
                        _sep,
                        '',
                        '🔢 Recibo: *' + pagamento.numero_pagamento + '*',
                        '📅 Data: *' + pagamento.data_pagamento.strftime('%d/%m/%Y') + '*',
                        '💳 Forma: *' + pagamento.get_forma_pagamento_display() + '*',
                        '💰 Valor: *R$ ' + '{:,.2f}'.format(pagamento.valor_pago) + '*',
                        '',
                        _sep,
                        '📍 *REFERENTE A:*',
                        _sep,
                        '',
                        '🏠 Imóvel: ' + _end,
                        '📋 ' + context.get('ref_label', '—'),
                        '',
                        _sep,
                        '',
                        '🔗 Ver recibo:',
                        recibo_url,
                        '',
                        '_Documento gerado via HABITAT PRO_',
                    ])
                    
                    # URL WhatsApp
                    mensagem_encoded = urllib.parse.quote(mensagem)
                    whatsapp_url = f'https://wa.me/{telefone_limpo}?text={mensagem_encoded}'
                    
                    # Salvar URL na sessão (mais seguro que cookie)
                    request.session['whatsapp_redirect'] = whatsapp_url
                    messages.success(request, '💬 Abrindo WhatsApp...')
                    
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Erro ao preparar WhatsApp: {e}')
                messages.error(request, f'❌ Erro ao enviar WhatsApp: {str(e)}')
    
    # Limpar redirect WhatsApp após renderizar (para não redirecionar novamente)
    whatsapp_redirect_temp = request.session.get('whatsapp_redirect')
    if whatsapp_redirect_temp and request.method == 'GET':
        # Manter na primeira renderização, limpar depois
        pass
    
    return render(request, 'admin/pagamento_recibo.html', context)
    
    
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from .models import Pagamento

@staff_member_required
def visualizar_recibo_pagamento(request, pagamento_id):
    """Exibe recibo em modal HTML bonito"""
    pagamento = get_object_or_404(Pagamento, pk=pagamento_id)
    
    context = {
        'pagamento': pagamento,
        'comanda': pagamento.comanda,
        'locacao': pagamento.comanda.locacao,
        'locatario': pagamento.comanda.locacao.locatario,
        'imovel': pagamento.comanda.locacao.imovel,
    }
    
    return render(request, 'admin/recibo_modal.html', context)



@staff_member_required
def comanda_web_view_OLD_DEPRECATED(request, comanda_id):
    """Página web da comanda com lógica inteligente de status"""
    from django.shortcuts import render, get_object_or_404
    from .models import Comanda
    from django.utils import timezone
    from decimal import Decimal
    
    comanda = get_object_or_404(Comanda, id=comanda_id)
    loc = comanda.locacao
    
    hoje = timezone.now().date()
    dias_atraso = (hoje - comanda.data_vencimento).days if hoje > comanda.data_vencimento else 0
    
    # ✅ LÓGICA INTELIGENTE DE STATUS E OBSERVAÇÕES
    status_comanda = comanda.status
    saldo = comanda.get_saldo() if hasattr(comanda, 'get_saldo') else (comanda.valor_pago - comanda.valor_total)
    
    # Determinar mensagem baseada no status
    if status_comanda == 'PAID' or status_comanda == 'PAGA':
        if saldo > 0:
            # Pago a maior - tem crédito
            mensagem_status = f'✅ Comanda QUITADA. Crédito de R$ {abs(saldo):,.2f} para o locatário.'
            tipo_alerta = 'success'
            mostrar_alerta_atraso = False
        else:
            # Pago exato
            mensagem_status = '✅ Comanda PAGA com sucesso.'
            tipo_alerta = 'success'
            mostrar_alerta_atraso = False
    elif status_comanda == 'PARTIAL':
        # Pagamento parcial
        saldo_restante = abs(saldo) if saldo < 0 else comanda.valor_total - comanda.valor_pago
        mensagem_status = f'⚡ Pagamento PARCIAL efetuado. Saldo restante: R$ {saldo_restante:,.2f}'
        tipo_alerta = 'warning'
        mostrar_alerta_atraso = dias_atraso > 0
    elif status_comanda == 'OVERDUE':
        # Vencida
        mensagem_status = f'⚠️ Comanda VENCIDA há {dias_atraso} dia(s).'
        tipo_alerta = 'danger'
        mostrar_alerta_atraso = True
    elif status_comanda == 'CANCELLED' or status_comanda == 'CANCELED':
        # Cancelada
        mensagem_status = '🚫 Comanda CANCELADA.'
        tipo_alerta = 'secondary'
        mostrar_alerta_atraso = False
    else:
        # Pendente
        if dias_atraso > 0:
            mensagem_status = f'⏳ Comanda PENDENTE (vencida há {dias_atraso} dia(s)).'
            tipo_alerta = 'danger'
            mostrar_alerta_atraso = True
        else:
            mensagem_status = '⏳ Comanda PENDENTE de pagamento.'
            tipo_alerta = 'info'
            mostrar_alerta_atraso = False
    
    # Adicionar frase de aviso
    aviso_pagamento = "Pague seus débitos em dia e evite multas, juros e outras correções conforme contrato de locação."
    
    context = {
        'titulo': f'Comanda {comanda.numero_comanda}',
        'comanda': comanda,
        'locacao': loc,
        'locatario_nome': loc.locatario.nome_razao_social,
        'imovel_endereco': f'{loc.imovel.endereco}, {loc.imovel.numero}',
        'numero_comanda': comanda.numero_comanda,
        'data_vencimento': comanda.data_vencimento.strftime('%d/%m/%Y'),
        'valor_aluguel': f'{comanda.valor_aluguel:,.2f}',
        'valor_condominio': f'{comanda.valor_condominio:,.2f}',
        'valor_iptu': f'{comanda.valor_iptu:,.2f}',
        'valor_multa': f'{comanda.valor_multa:,.2f}',
        'valor_juros': f'{comanda.valor_juros:,.2f}',
        'valor_total': f'{comanda.valor_total:,.2f}',
        'valor_pago': f'{comanda.valor_pago:,.2f}',
        'saldo': f'{abs(saldo):,.2f}',
        'tem_multa_juros': (comanda.valor_multa > 0 or comanda.valor_juros > 0),
        'dias_atraso': dias_atraso,
        'status_comanda': status_comanda,
        'mensagem_status': mensagem_status,
        'tipo_alerta': tipo_alerta,
        'mostrar_alerta_atraso': mostrar_alerta_atraso,
        'aviso_pagamento': aviso_pagamento,
        'mensagem': f'Comanda referente ao imóvel {loc.imovel.endereco}.',
        'observacoes': comanda.observacoes,  # DEV_21.8 - Observações em HTML/Email
        'outros_debitos': f"{comanda.outros_debitos:,.2f}" if comanda.outros_debitos > 0 else None,
        'outros_creditos': f"{comanda.outros_creditos:,.2f}" if comanda.outros_creditos > 0 else None,
    }
    
    return render(request, 'admin/comanda_web.html', context)


@staff_member_required
def enviar_comanda_email(request, comanda_id):
    """Envia comanda por email com detalhamento completo e aviso"""
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from django.core.mail import EmailMessage
    from django.conf import settings
    from .models import Comanda
    from decimal import Decimal
    import socket
    
    comanda = get_object_or_404(Comanda, id=comanda_id)
    loc = comanda.locacao.locatario
    imovel = comanda.locacao.imovel
    
    if not loc.email:
        messages.error(request, f'❌ Locatário sem email!')
        return redirect('admin:core_comanda_changelist')
    
    try:
        # ⚡ TIMEOUT DE 10 SEGUNDOS - Evitar worker timeout
        socket.setdefaulttimeout(10)

        # 🔧 DEV_21.8.11: Usar mesma URL do WhatsApp (com token e fallback)
        from .views_comanda_web import gerar_token_comanda
        token = gerar_token_comanda(str(comanda.id))
        url = request.build_absolute_uri(f'/comanda/{comanda.id}/{token}/')
        
        # ✅ LÓGICA INTELIGENTE DE STATUS
        status_comanda = comanda.status
        saldo = comanda.get_saldo() if hasattr(comanda, 'get_saldo') else (comanda.valor_pago - comanda.valor_total)
        
        # Determinar observação baseada no status
        if status_comanda in ['PAID', 'PAGA']:
            if saldo > 0:
                obs_status = f'\n✅ COMANDA QUITADA\nCrédito de R$ {abs(saldo):,.2f} para o locatário.\n'
            else:
                obs_status = '\n✅ COMANDA PAGA\n'
        elif status_comanda == 'PARTIAL':
            saldo_restante = abs(saldo) if saldo < 0 else comanda.valor_total - comanda.valor_pago
            obs_status = f'\n⚡ PAGAMENTO PARCIAL EFETUADO\nSaldo restante: R$ {saldo_restante:,.2f}\n'
        elif status_comanda == 'OVERDUE':
            from django.utils import timezone
            dias = (timezone.now().date() - comanda.data_vencimento).days
            obs_status = f'\n⚠️ COMANDA VENCIDA\nVencida há {dias} dia(s).\n'
        else:
            obs_status = '\n⏳ COMANDA PENDENTE DE PAGAMENTO\n'
        
        corpo = f'''
Prezado(a) {loc.nome_razao_social},

Segue comanda de pagamento referente ao imóvel:
📍 {imovel.endereco}, {imovel.numero}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 DETALHAMENTO DA COMANDA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Comanda Nº: {comanda.numero_comanda}
Vencimento: {comanda.data_vencimento.strftime('%d/%m/%Y')}

VALORES:
  • Aluguel: R$ {comanda.valor_aluguel:,.2f}
  • Condomínio: R$ {comanda.valor_condominio:,.2f}
  • IPTU: R$ {comanda.valor_iptu:,.2f}'''

        # Adicionar outros débitos/créditos se houver
        if comanda.outros_debitos > 0:
            corpo += f'''
  • Outras despesas: R$ {comanda.outros_debitos:,.2f}'''
        
        if comanda.outros_creditos > 0:
            corpo += f'''
  • Créditos: R$ -{comanda.outros_creditos:,.2f}'''

        # Adicionar multa/juros se houver
        if comanda.valor_multa > 0 or comanda.valor_juros > 0:
            corpo += f'''
  • Multa (10%): R$ {comanda.valor_multa:,.2f}
  • Juros (1% a.m.): R$ {comanda.valor_juros:,.2f}'''

        corpo += f'''

TOTAL: R$ {comanda.valor_total:,.2f}
{obs_status}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
'''
        
        # ✅ NOVO DEV_20: Campo Comentários (Observações)
        if comanda.observacoes and comanda.observacoes.strip():
            corpo += f'''
📝 COMENTÁRIOS:
{comanda.observacoes.strip()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
'''
        
        corpo += f'''
🔗 Ver comanda completa:
{url}

⚠️ IMPORTANTE:
Pague seus débitos em dia e evite multas, juros e outras 
correções conforme contrato de locação.

Atenciosamente,
HABITAT PRO v1.0
Sistema de Gestão Imobiliária
'''
        
        email = EmailMessage(
            subject=f'Comanda de Pagamento - {comanda.numero_comanda}',
            body=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[loc.email],
        )
        email.send()
        messages.success(request, f'📧 Email enviado para {loc.email}!')
    except (Exception, socket.timeout) as e:
        if isinstance(e, socket.timeout):
            messages.error(request, '⏱️ Timeout: Servidor de email não respondeu em 10 segundos')
        else:
            messages.error(request, f'❌ Erro ao enviar email: {str(e)}')
    
    finally:
        # 🔄 Restaurar timeout padrão
        socket.setdefaulttimeout(None)

    return redirect('admin:core_comanda_changelist')


# ══════════════════════════════════════════════════════════════════
# RECIBO PÚBLICO — Link seguro via token UUID (válido 30 dias)
# Isolado: sem links para admin, Railway ou sistema
# ══════════════════════════════════════════════════════════════════

def recibo_publico(request, token):
    """
    Página pública do recibo via token UUID.
    SEGURANÇA: isolada, sem acesso ao sistema.
    """
    from django.shortcuts import render
    from django.utils import timezone
    from django.http import Http404
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Validar UUID antes de query
        import uuid as uuid_lib
        try:
            uuid_lib.UUID(str(token))
        except ValueError:
            logger.warning(f'Token inválido (não UUID): {token}')
            raise Http404("Link inválido")
        
        # Buscar pagamento — token pode não existir (pagamento sem token gerado)
        try:
            pagamento = Pagamento.objects.get(token=token)
        except Pagamento.DoesNotExist:
            return render(request, 'recibo_expirado.html', {
                'numero_pagamento': 'desconhecido',
            })
        
        # Verificar expiração
        if not pagamento.token_expira_em or pagamento.token_expira_em < timezone.now():
            return render(request, 'recibo_expirado.html', {
                'numero_pagamento': pagamento.numero_pagamento,
            })
        
        # Resolver contexto polimórfico
        if pagamento.comanda_id:
            comanda   = pagamento.comanda
            locacao   = comanda.locacao   if comanda else None
            locatario = locacao.locatario if locacao else None
            imovel    = locacao.imovel    if locacao else None
            if comanda and locacao:
                ref_label = ('Comanda ' + comanda.numero_comanda
                             + ' | Vcto ' + comanda.data_vencimento.strftime('%d/%m/%Y'))
            else:
                ref_label = 'Aluguel'
        elif pagamento.content_type_id and pagamento.object_id:
            comanda   = None
            _ref      = pagamento.comanda_ref
            _rs       = _ref.rescisao if (_ref and hasattr(_ref, 'rescisao')) else None
            locacao   = _rs.locacao   if _rs else None
            locatario = locacao.locatario if locacao else None
            imovel    = locacao.imovel    if locacao else None
            if _ref and _rs:
                ref_label = ('Rescisão | Parcela ' + str(_ref.numero_parcela)
                             + ' de ' + str(_rs.quantidade_parcelas)
                             + ' | Vcto ' + _ref.data_vencimento.strftime('%d/%m/%Y'))
            else:
                ref_label = 'Rescisão'
        else:
            comanda = locacao = locatario = imovel = None
            ref_label = '—'
        
        context = {
            'pagamento': pagamento,
            'locatario': locatario,
            'imovel': imovel,
            'ref_label': ref_label,
            'data_br': pagamento.data_pagamento.strftime('%d/%m/%Y') if pagamento.data_pagamento else '—',
        }
        
        # Log acesso (auditoria)
        logger.info(f'Recibo público acessado: {pagamento.numero_pagamento} | Token: {token}')
        
        return render(request, 'recibo_publico.html', context)
    
    except Exception as e:
        logger.error(f'Erro recibo público token {token}: {e}')
        raise Http404("Recibo não encontrado")


def recibo_publico_pdf(request, token):
    """
    PDF do recibo via token UUID.
    Gera PDF nativo (WeasyPrint) em memória e retorna diretamente.
    """
    from django.shortcuts import render
    from django.template.loader import render_to_string
    from django.http import HttpResponse, Http404
    from django.utils import timezone
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Validar UUID
        import uuid as uuid_lib
        try:
            uuid_lib.UUID(str(token))
        except ValueError:
            raise Http404("Link inválido")
        
        pagamento = get_object_or_404(Pagamento, token=token)
        
        # Verificar expiração
        if not pagamento.token_expira_em or pagamento.token_expira_em < timezone.now():
            raise Http404("Link expirado")
        
        # Resolver contexto (mesmo código de recibo_publico)
        if pagamento.comanda_id:
            comanda   = pagamento.comanda
            locacao   = comanda.locacao   if comanda else None
            locatario = locacao.locatario if locacao else None
            imovel    = locacao.imovel    if locacao else None
            if comanda and locacao:
                ref_label = ('Comanda ' + comanda.numero_comanda
                             + ' | Vcto ' + comanda.data_vencimento.strftime('%d/%m/%Y'))
            else:
                ref_label = 'Aluguel'
        elif pagamento.content_type_id and pagamento.object_id:
            comanda   = None
            _ref      = pagamento.comanda_ref
            _rs       = _ref.rescisao if (_ref and hasattr(_ref, 'rescisao')) else None
            locacao   = _rs.locacao   if _rs else None
            locatario = locacao.locatario if locacao else None
            imovel    = locacao.imovel    if locacao else None
            if _ref and _rs:
                ref_label = ('Rescisão | Parcela ' + str(_ref.numero_parcela)
                             + ' de ' + str(_rs.quantidade_parcelas)
                             + ' | Vcto ' + _ref.data_vencimento.strftime('%d/%m/%Y'))
            else:
                ref_label = 'Rescisão'
        else:
            locacao = locatario = imovel = None
            ref_label = '—'
        
        context = {
            'pagamento': pagamento,
            'locatario': locatario,
            'imovel': imovel,
            'ref_label': ref_label,
            'data_br': pagamento.data_pagamento.strftime('%d/%m/%Y') if pagamento.data_pagamento else '—',
        }
        
        # Gerar DOCX polimórfico via DocumentGenerator
        from .document_generator import DocumentGenerator
        import tempfile
        import subprocess
        
        generator = DocumentGenerator()
        
        try:
            # Gerar DOCX
            if hasattr(generator, 'gerar_recibo_polimorfico'):
                docx_filename = generator.gerar_recibo_polimorfico(pagamento.id)
            else:
                docx_filename = generator.gerar_recibo_pagamento(pagamento.id)
            
            docx_path = os.path.join(generator.output_dir, docx_filename)
            
            # Converter DOCX → PDF via LibreOffice (estratégia dos contratos)
            with tempfile.TemporaryDirectory() as tmpdir:
                try:
                    # LibreOffice headless
                    subprocess.run([
                        'libreoffice',
                        '--headless',
                        '--convert-to', 'pdf',
                        '--outdir', tmpdir,
                        docx_path
                    ], check=True, capture_output=True, timeout=30)
                    
                    # Ler PDF gerado
                    pdf_filename = docx_filename.replace('.docx', '.pdf')
                    pdf_path = os.path.join(tmpdir, pdf_filename)
                    
                    with open(pdf_path, 'rb') as f:
                        pdf_data = f.read()
                    
                    response = HttpResponse(pdf_data, content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="recibo_{pagamento.numero_pagamento}.pdf"'
                    
                    logger.info(f'PDF gerado (LibreOffice): {pagamento.numero_pagamento} | Token: {token}')
                    return response
                
                except (FileNotFoundError, subprocess.CalledProcessError):
                    # LibreOffice não disponível → fallback DOCX
                    logger.warning('LibreOffice não disponível. Retornando DOCX.')
                    
                    with open(docx_path, 'rb') as f:
                        docx_data = f.read()
                    
                    response = HttpResponse(
                        docx_data,
                        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    )
                    response['Content-Disposition'] = f'attachment; filename="recibo_{pagamento.numero_pagamento}.docx"'
                    return response
        
        except Exception as e:
            logger.error(f'Erro geração documento: {e}')
            raise Http404("Erro ao gerar documento")
    
    except Exception as e:
        logger.error(f'Erro PDF público token {token}: {e}')
        raise Http404("Erro ao gerar PDF")
