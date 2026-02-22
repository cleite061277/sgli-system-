"""
════════════════════════════════════════════════════════════════════
MÓDULO: RESCISÃO DE CONTRATOS - ADMIN
Arquivo: core/admin_rescisao.py
Descrição: Interface administrativa completa para rescisões
Autor: Habitat Pro - Desenvolvimento
Data: 2026-02-11
════════════════════════════════════════════════════════════════════
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from decimal import Decimal

from .models_rescisao import RescisaoContrato, ComandaRescisao


# ════════════════════════════════════════════════════════════════
# ADMIN: ComandaRescisao
# ════════════════════════════════════════════════════════════════
from core.admin import PagamentoInline


@admin.register(ComandaRescisao)
class ComandaRescisaoAdmin(admin.ModelAdmin):
    """
    Admin para comandas de rescisão.
    Interface similar às comandas de aluguel.
    """

    inlines = [PagamentoInline]

    def save_formset(self, request, form, formset, change):
        """
        Preenche usuario_registro e GenericFK automaticamente.
        Idêntico ao ComandaAdmin (admin.py linha 724).
        Obrigatório pois PagamentoInline é GenericTabularInline
        e não tem acesso ao request.user diretamente.
        """
        instances = formset.save(commit=False)

        if not getattr(request.user, 'is_authenticated', False):
            raise ValueError("Usuário não autenticado")

        user_pk = getattr(request.user, 'pk', None)
        if not user_pk:
            raise ValueError("Usuário sem PK válido")

        for instance in instances:
            # Preencher usuario_registro (campo NOT NULL)
            if hasattr(instance, 'usuario_registro_id'):
                if not getattr(instance, 'usuario_registro_id', None):
                    instance.usuario_registro_id = user_pk

            # Preencher GenericFK: content_type + object_id
            if hasattr(instance, 'content_type_id'):
                if not getattr(instance, 'content_type_id', None):
                    from django.contrib.contenttypes.models import ContentType
                    from .models_rescisao import ComandaRescisao
                    instance.content_type = ContentType.objects.get_for_model(ComandaRescisao)
                    instance.object_id = form.instance.pk

            instance.save()

        formset.save_m2m()

    
    list_display = [
        'id_display',
        'rescisao_link',
        'parcela_display',
        'valor_formatado',
        'data_vencimento',
        'status_badge',
        'situacao_display',
        'comprovante_badge',
        'acoes_rapidas'
    ]
    
    list_filter = [
        'status',
        'data_vencimento',
        'notificacao_enviada',
        'notificacao_atraso_enviada',
    ]
    
    search_fields = [
        'rescisao__locacao__numero_contrato',
        'rescisao__locacao__locatario__nome_razao_social',
        'descricao',
    ]
    
    readonly_fields = [
        'token_publico',
        'token_expira_em',
        'token_acessos',
        'token_ultimo_acesso',
        'notificacao_enviada',
        'data_notificacao',
        'notificacao_atraso_enviada',
        'data_notificacao_atraso',
        'created_at',
        'updated_at',
        'link_publico_display',
        'link_whatsapp_display',
    ]
    
    fieldsets = (
        ('📋 Informações Básicas', {
            'fields': (
                'rescisao',
                'numero_parcela',
                'descricao',
            )
        }),
        ('💰 Valores e Datas', {
            'fields': (
                'valor',
                'data_vencimento',
                'data_pagamento',
                'status',
            )
        }),
        ('📎 Comprovante', {
            'fields': ('comprovante',),
        }),
        ('🔗 Acesso Público', {
            'fields': (
                'token_publico',
                'token_expira_em',
                'token_acessos',
                'token_ultimo_acesso',
                'link_publico_display',
                'link_whatsapp_display',
            ),
            'classes': ('collapse',),
        }),
        ('📧 Notificações', {
            'fields': (
                'notificacao_enviada',
                'data_notificacao',
                'notificacao_atraso_enviada',
                'data_notificacao_atraso',
            ),
            'classes': ('collapse',),
        }),
        ('💳 Pagamento Online (Futuro)', {
            'fields': (
                'gateway_payment_id',
                'pix_qrcode',
                'boleto_url',
            ),
            'classes': ('collapse',),
        }),
        ('🕐 Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = [
        'enviar_cobranca_email',
        'enviar_atraso_email',
        'gerar_links_whatsapp',
        'marcar_como_pago',
        'renovar_tokens',
    ]
    
    # ========================================
    # LIST DISPLAY METHODS
    # ========================================
    
    def id_display(self, obj):
        return f"#{str(obj.id)[:8]}"
    id_display.short_description = 'ID'
    
    def rescisao_link(self, obj):
        url = reverse('admin:core_rescisaocontrato_change', args=[obj.rescisao.id])
        return format_html(
            '<a href="{}" title="Ver rescisão completa">Rescisão {}</a>',
            url,
            str(obj.rescisao.id)[:8]
        )
    rescisao_link.short_description = 'Rescisão'
    
    def parcela_display(self, obj):
        return f"{obj.numero_parcela}/{obj.rescisao.quantidade_parcelas}"
    parcela_display.short_description = 'Parcela'
    
    def valor_formatado(self, obj):
        return obj.valor_formatado
    valor_formatado.short_description = 'Valor'
    valor_formatado.admin_order_field = 'valor'
    
    def status_badge(self, obj):
        cores = {
            'PENDENTE': '#FFA500',
            'PAGO': '#28A745',
            'ATRASADO': '#DC3545',
            'CANCELADO': '#6C757D',
        }
        cor = cores.get(obj.status, '#6C757D')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:3px; font-weight:bold; font-size:11px;">{}</span>',
            cor,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def situacao_display(self, obj):
        if obj.status == 'PAGO':
            return format_html('<span style="color:green;">✅ Pago</span>')
        elif obj.esta_atrasada:
            return format_html(
                '<span style="color:red; font-weight:bold;">⚠️ {} dia(s)</span>',
                obj.dias_atraso
            )
        else:
            dias = obj.dias_para_vencimento
            if dias == 0:
                return format_html('<span style="color:orange;">⏰ Vence hoje</span>')
            elif dias < 0:
                return format_html('<span style="color:red;">Vencido</span>')
            else:
                return format_html('🕒 {} dia(s)', dias)
    situacao_display.short_description = 'Situação'
    
    def comprovante_badge(self, obj):
        if obj.comprovante:
            return format_html(
                '<a href="{}" target="_blank" style="color:green;">📎 Ver</a>',
                obj.comprovante.url
            )
        return format_html('<span style="color:#999;">—</span>')
    comprovante_badge.short_description = 'Comprovante'
    
    def acoes_rapidas(self, obj):
        if obj.status in ['PENDENTE', 'ATRASADO']:
            return format_html(
                '<a class="button" style="font-size:11px; padding:5px 10px;" '
                'href="{}">💰 Registrar Pagamento</a>',
                reverse('admin:core_comandarescisao_change', args=[obj.id])
            )
        return '—'
    acoes_rapidas.short_description = 'Ações'
    
    def link_publico_display(self, obj):
        from django.conf import settings
        url = f"{settings.SITE_URL}/comanda-rescisao/{obj.token_publico}/"
        return format_html(
            '<a href="{}" target="_blank">{}</a><br>'
            '<small style="color:#666;">Expira: {}</small>',
            url,
            url,
            obj.token_expira_em.strftime('%d/%m/%Y %H:%M') if obj.token_expira_em else 'Nunca'
        )
    link_publico_display.short_description = 'Link Público'
    
    def link_whatsapp_display(self, obj):
        link = obj.gerar_link_whatsapp()
        return format_html(
            '<a href="{}" target="_blank" class="button" '
            'style="background:#25D366; color:white;">📱 Abrir WhatsApp</a>',
            link
        )
    link_whatsapp_display.short_description = 'WhatsApp'
    
    # ========================================
    # ACTIONS
    # ========================================
    
    @admin.action(description='📧 Enviar cobrança por email')
    def enviar_cobranca_email(self, request, queryset):
        
        enviados = 0
        erros = 0
        
        filtradas = queryset.filter(status__in=['PENDENTE', 'ATRASADO'])
        
        for comanda in filtradas:
            try:
                resultado = comanda.enviar_notificacao_cobranca()
                enviados += 1
            except Exception as e:
                import traceback
                traceback.print_exc()
                erros += 1
        
        
        # Verificar se há comandas pagas selecionadas
        comandas_pagas = queryset.exclude(status__in=['PENDENTE', 'ATRASADO']).count()
        
        if comandas_pagas > 0:
            self.message_user(
                request, 
                f'ℹ️ {comandas_pagas} comanda(s) com status PAGO foram ignoradas. '
                f'Emails só são enviados para comandas PENDENTES ou ATRASADAS.',
                level='WARNING'
            )
        
        if enviados > 0:
            self.message_user(request, f'✅ {enviados} email(s) enviado(s)!', level='SUCCESS')
        if erros > 0:
            self.message_user(request, f'⚠️ {erros} erro(s) ao enviar', level='WARNING')
        
        # Se nenhuma foi enviada e havia comandas selecionadas
        if enviados == 0 and queryset.count() > 0 and comandas_pagas == queryset.count():
            self.message_user(
                request,
                '⚠️ Nenhum email enviado. Todas as comandas selecionadas estão com status PAGO.',
                level='WARNING'
            )
    
    @admin.action(description='⚠️ Enviar notificação de atraso')
    def enviar_atraso_email(self, request, queryset):
        enviados = 0
        
        for comanda in queryset.filter(status__in=['PENDENTE', 'ATRASADO']):
            if comanda.esta_atrasada:
                try:
                    comanda.enviar_notificacao_atraso()
                    enviados += 1
                except:
                    pass
        
        self.message_user(request, f'✅ {enviados} notificação(ões) de atraso enviada(s)!', level='SUCCESS')
    
    @admin.action(description='📱 Gerar links WhatsApp')
    def gerar_links_whatsapp(self, request, queryset):
        from django.utils.safestring import mark_safe
        
        html = '<div style="font-family:Arial;"><h3>📱 Links WhatsApp Gerados</h3>'
        
        for comanda in queryset:
            link = comanda.gerar_link_whatsapp()
            destinatario = comanda.get_destinatario()
            
            html += f"""
            <div style="margin:15px 0; padding:15px; background:#f5f5f5; border-left:4px solid #25D366;">
                <p><strong>Parcela:</strong> {comanda.numero_parcela}/{comanda.rescisao.quantidade_parcelas}<br>
                <strong>Destinatário:</strong> {destinatario.nome_razao_social}<br>
                <strong>Valor:</strong> {comanda.valor_formatado}<br>
                <strong>Vencimento:</strong> {comanda.data_vencimento.strftime('%d/%m/%Y')}</p>
                <a href="{link}" target="_blank" 
                   style="background:#25D366; color:white; padding:10px 20px; text-decoration:none; 
                          border-radius:5px; display:inline-block; font-weight:bold;">
                    Abrir WhatsApp ➜
                </a>
            </div>
            """
        
        html += '</div>'
        self.message_user(request, mark_safe(html), level='SUCCESS')
    
    @admin.action(description='✅ Marcar como pago')
    def marcar_como_pago(self, request, queryset):
        from datetime import date
        count = 0
        
        for comanda in queryset.filter(status__in=['PENDENTE', 'ATRASADO']):
            comanda.registrar_pagamento(date.today())
            count += 1
        
        self.message_user(request, f'✅ {count} comanda(s) marcada(s) como paga(s)!', level='SUCCESS')
    
    @admin.action(description='🔄 Renovar tokens (30 dias)')
    def renovar_tokens(self, request, queryset):
        count = queryset.count()
        
        for comanda in queryset:
            comanda.renovar_token(dias_validade=30)
        
        self.message_user(request, f'✅ {count} token(s) renovado(s) por 30 dias!', level='SUCCESS')


# ════════════════════════════════════════════════════════════════
# ADMIN: RescisaoContrato
# ════════════════════════════════════════════════════════════════

@admin.register(RescisaoContrato)
class RescisaoContratoAdmin(admin.ModelAdmin):
    """
    Admin principal para gerenciar rescisões de contrato.
    Interface completa com workflow e ações automatizadas.
    """
    
    list_display = [
        'id_display',
        'contrato_link',
        'locatario_display',
        'tipo',
        'data_desocupacao',
        'status_badge',
        'total_devido_display',
        'total_pago_display',
        'saldo_display',
        'confirmado_badge',
        'acoes_rapidas'
    ]
    
    list_filter = [
        'status',
        'tipo',
        'motivo',
        'confirmado_por_inquilino',
        'data_solicitacao',
        'data_desocupacao',
    ]
    
    search_fields = [
        'locacao__numero_contrato',
        'locacao__locatario__nome_razao_social',
        'locacao__imovel__endereco',
    ]
    
    readonly_fields = [
        'data_solicitacao',
        'token_confirmacao',
        'token_confirmacao_expira',
        'data_confirmacao_inquilino',
        'confirmado_por_inquilino',
        'created_at',
        'updated_at',
        'link_confirmacao_display',
        'log_solicitacao_display',
        'log_confirmacao_display',
        'log_comunicacoes_display',
        'comandas_resumo',
        'percentual_pago_display',
    ]
    
    fieldsets = (
        ('📋 Dados Básicos', {
            'fields': (
                'locacao',
                'solicitante',
                'tipo',
                'motivo',
                'data_solicitacao',
                'data_desocupacao',
                'status',
            )
        }),
        ('📝 Observações', {
            'fields': (
                'observacoes_solicitacao',
                'observacoes_vistoria',
            )
        }),
        ('🏠 Vistoria', {
            'fields': (
                'data_vistoria',
                'imovel_conforme',
                'avarias_detectadas',
                'custo_reparos',
            )
        }),
        ('💰 Valores Calculados', {
            'fields': (
                'multa_rescisoria',
                'valor_aluguel_proporcional',
                'valor_agua',
                'valor_luz',
                'valor_gas',
                'valor_condominio',
                'outras_despesas',
                'valor_caucao',
            ),
            'description': 'Valores calculados automaticamente. Use a action "Calcular Valores" para recalcular.'
        }),
        ('📊 Totais', {
            'fields': (
                'valor_total_devido',
                'valor_total_pago',
                'percentual_pago_display',
            )
        }),
        ('💳 Parcelamento', {
            'fields': (
                'quantidade_parcelas',
                'valor_parcela',
                'comandas_resumo',
            )
        }),
        ('📄 Documentos', {
            'fields': (
                'termo_recebimento_chaves',
                'laudo_vistoria',
            )
        }),
        ('✅ Confirmação do Inquilino', {
            'fields': (
                'confirmado_por_inquilino',
                'data_confirmacao_inquilino',
                'token_confirmacao',
                'token_confirmacao_expira',
                'link_confirmacao_display',
            ),
            'classes': ('collapse',),
        }),
        ('📋 Logs (Uso Judicial)', {
            'fields': (
                'log_solicitacao_display',
                'log_confirmacao_display',
                'log_comunicacoes_display',
            ),
            'classes': ('collapse',),
        }),
        ('🕐 Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = [
        'calcular_valores',
        'gerar_documentos',
        'gerar_comandas',
        'enviar_link_confirmacao_email',
        'gerar_link_confirmacao_whatsapp',
        'finalizar_rescisao',
    ]
    
    # ========================================
    # LIST DISPLAY METHODS
    # ========================================
    
    def id_display(self, obj):
        return f"#{str(obj.id)[:8]}"
    id_display.short_description = 'ID'
    
    def contrato_link(self, obj):
        url = reverse('admin:core_locacao_change', args=[obj.locacao.id])
        return format_html(
            '<a href="{}" title="Ver contrato">{}</a>',
            url,
            obj.locacao.numero_contrato
        )
    contrato_link.short_description = 'Contrato'
    
    def locatario_display(self, obj):
        return obj.locacao.locatario.nome_razao_social
    locatario_display.short_description = 'Locatário'
    
    def status_badge(self, obj):
        cores = {
            'SOLICITADA': '#17A2B8',
            'EM_ANALISE': '#FFC107',
            'APROVADA': '#28A745',
            'VISTORIA_AGENDADA': '#17A2B8',
            'VISTORIA_REALIZADA': '#17A2B8',
            'DOCUMENTOS_GERADOS': '#FFC107',
            'AGUARDANDO_PAGAMENTO': '#FFA500',
            'FINALIZADA': '#28A745',
            'CANCELADA': '#DC3545',
        }
        cor = cores.get(obj.status, '#6C757D')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; '
            'border-radius:3px; font-weight:bold; font-size:11px;">{}</span>',
            cor,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def total_devido_display(self, obj):
        return f"R$ {obj.valor_total_devido:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    total_devido_display.short_description = 'Total Devido'
    total_devido_display.admin_order_field = 'valor_total_devido'
    
    def total_pago_display(self, obj):
        return f"R$ {obj.valor_total_pago:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    total_pago_display.short_description = 'Total Pago'
    total_pago_display.admin_order_field = 'valor_total_pago'
    
    def saldo_display(self, obj):
        saldo = obj.saldo_devedor
        cor = 'green' if saldo == 0 else 'red'
        return format_html(
            '<span style="color:{}; font-weight:bold;">R$ {}</span>',
            cor,
            f"{saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
    saldo_display.short_description = 'Saldo'
    
    def confirmado_badge(self, obj):
        if obj.confirmado_por_inquilino:
            return format_html(
                '<span style="color:green; font-weight:bold;">✅ Confirmado</span><br>'
                '<small style="color:#666;">{}</small>',
                obj.data_confirmacao_inquilino.strftime('%d/%m/%Y %H:%M') if obj.data_confirmacao_inquilino else ''
            )
        elif obj.token_confirmacao_valido:
            return format_html('<span style="color:orange;">⏳ Aguardando</span>')
        else:
            return format_html('<span style="color:red;">❌ Token expirado</span>')
    confirmado_badge.short_description = 'Confirmação'
    
    def acoes_rapidas(self, obj):
        botoes = []
        
        if obj.status == 'VISTORIA_REALIZADA':
            botoes.append('<a class="button" style="font-size:11px;">📄 Gerar Docs</a>')
        
        if obj.status == 'DOCUMENTOS_GERADOS':
            botoes.append('<a class="button" style="font-size:11px;">📋 Gerar Comandas</a>')
        
        if obj.termo_recebimento_chaves:
            botoes.append(
                f'<a class="button" style="font-size:11px;" href="{obj.termo_recebimento_chaves.url}" target="_blank">📥 Termo</a>'
            )
        
        return format_html(' '.join(botoes)) if botoes else '—'
    acoes_rapidas.short_description = 'Ações'
    
    # ========================================
    # READONLY FIELDS METHODS
    # ========================================
    
    def link_confirmacao_display(self, obj):
        from django.conf import settings
        url = f"{settings.SITE_URL}/rescisao/confirmar/{obj.token_confirmacao}/"
        
        if obj.confirmado_por_inquilino:
            return format_html(
                '<div style="color:green;">✅ Já confirmado em {}</div>',
                obj.data_confirmacao_inquilino.strftime('%d/%m/%Y %H:%M') if obj.data_confirmacao_inquilino else ''
            )
        
        return format_html(
            '<a href="{}" target="_blank">{}</a><br>'
            '<small style="color:#666;">Expira: {}</small><br><br>'
            '<a href="{}" target="_blank" class="button" style="background:#007bff; color:white;">🔗 Copiar Link</a>',
            url, url,
            obj.token_confirmacao_expira.strftime('%d/%m/%Y %H:%M') if obj.token_confirmacao_expira else 'Nunca',
            url
        )
    link_confirmacao_display.short_description = 'Link de Confirmação'
    
    def comandas_resumo(self, obj):
        comandas = obj.comandas.all()
        if not comandas:
            return 'Nenhuma comanda gerada ainda.'
        
        html = '<table style="width:100%; border-collapse:collapse;">'
        html += '<tr style="background:#f0f0f0;"><th>Parcela</th><th>Valor</th><th>Vencimento</th><th>Status</th></tr>'
        
        for cmd in comandas:
            cor_status = {'PAGO': 'green', 'PENDENTE': 'orange', 'ATRASADO': 'red'}.get(cmd.status, 'gray')
            html += f'''
            <tr style="border-bottom:1px solid #ddd;">
                <td style="padding:5px;">{cmd.numero_parcela}/{obj.quantidade_parcelas}</td>
                <td style="padding:5px;">{cmd.valor_formatado}</td>
                <td style="padding:5px;">{cmd.data_vencimento.strftime('%d/%m/%Y')}</td>
                <td style="padding:5px; color:{cor_status}; font-weight:bold;">{cmd.get_status_display()}</td>
            </tr>
            '''
        
        html += '</table>'
        return format_html(html)
    comandas_resumo.short_description = 'Comandas'
    
    def percentual_pago_display(self, obj):
        perc = obj.percentual_pago
        return format_html(
            '<div style="background:#e0e0e0; border-radius:10px; height:20px; position:relative;">'
            '<div style="background:#28a745; width:{}%; height:100%; border-radius:10px;"></div>'
            '<span style="position:absolute; top:0; left:50%; transform:translateX(-50%); font-weight:bold; font-size:11px;">{:.1f}%</span>'
            '</div>',
            perc, perc
        )
    percentual_pago_display.short_description = 'Progresso'
    
    def log_solicitacao_display(self, obj):
        if not obj.log_solicitacao:
            return 'Nenhum log ainda.'
        
        import json
        return format_html('<pre style="background:#f5f5f5; padding:10px; border-radius:5px;">{}</pre>', 
                          json.dumps(obj.log_solicitacao, indent=2, ensure_ascii=False))
    log_solicitacao_display.short_description = 'Log Solicitação'
    
    def log_confirmacao_display(self, obj):
        if not obj.log_confirmacao_inquilino:
            return 'Aguardando confirmação.'
        
        import json
        return format_html('<pre style="background:#f5f5f5; padding:10px; border-radius:5px;">{}</pre>',
                          json.dumps(obj.log_confirmacao_inquilino, indent=2, ensure_ascii=False))
    log_confirmacao_display.short_description = 'Log Confirmação'
    
    def log_comunicacoes_display(self, obj):
        if not obj.log_comunicacoes:
            return 'Nenhuma comunicação enviada.'
        
        html = '<table style="width:100%; border-collapse:collapse; font-size:12px;">'
        html += '<tr style="background:#f0f0f0;"><th>Data</th><th>Tipo</th><th>Destinatário</th><th>Status</th></tr>'
        
        for comm in obj.log_comunicacoes:
            html += f'''
            <tr style="border-bottom:1px solid #ddd;">
                <td style="padding:5px;">{comm.get('data', '')[:16]}</td>
                <td style="padding:5px;">{comm.get('tipo', '')}</td>
                <td style="padding:5px;">{comm.get('destinatario', '')}</td>
                <td style="padding:5px; color:green;">{comm.get('status', '')}</td>
            </tr>
            '''
        
        html += '</table>'
        return format_html(html)
    log_comunicacoes_display.short_description = 'Log Comunicações'
    
    # ========================================
    # ACTIONS
    # ========================================
    
    @admin.action(description='🧮 Calcular valores automaticamente')
    def calcular_valores(self, request, queryset):
        count = 0
        for rescisao in queryset:
            rescisao.calcular_valores()
            count += 1
        
        self.message_user(request, f'✅ {count} rescisão(ões) recalculada(s)!', level='SUCCESS')
    
    @admin.action(description='📄 Gerar documentos (Termo)')
    def gerar_documentos(self, request, queryset):
        gerados = 0
        erros = 0
        
        for rescisao in queryset:
            try:
                rescisao.gerar_termo_recebimento_chaves()
                gerados += 1
            except Exception as e:
                erros += 1
                self.message_user(request, f'❌ Erro em {rescisao}: {e}', level='ERROR')
        
        if gerados > 0:
            self.message_user(request, f'✅ {gerados} documento(s) gerado(s)!', level='SUCCESS')
    
    @admin.action(description='📋 Gerar comandas de pagamento')
    def gerar_comandas(self, request, queryset):
        gerados = 0
        
        for rescisao in queryset:
            rescisao.gerar_comandas_rescisao()
            gerados += 1
        
        self.message_user(request, f'✅ Comandas geradas para {gerados} rescisão(ões)!', level='SUCCESS')
    
    @admin.action(description='📧 Enviar link de confirmação (Email)')
    def enviar_link_confirmacao_email(self, request, queryset):
        enviados = 0
        
        for rescisao in queryset:
            if not rescisao.confirmado_por_inquilino:
                try:
                    from core.services.email_service import EmailService
                    EmailService.enviar_confirmacao_rescisao(rescisao)
                    enviados += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f'❌ Erro ao enviar para {rescisao.locacao.locatario.nome_razao_social}: {e}',
                        level='ERROR'
                    )
                except Exception as e:
                    pass
        
        self.message_user(request, f'✅ {enviados} email(s) enviado(s)!', level='SUCCESS')
    
    @admin.action(description='📱 Gerar link de confirmação (WhatsApp)')
    def gerar_link_confirmacao_whatsapp(self, request, queryset):
        from django.utils.safestring import mark_safe
        from django.conf import settings
        import urllib.parse
        
        html = '<div style="font-family:Arial;"><h3>📱 Links WhatsApp - Confirmação de Rescisão</h3>'
        
        for rescisao in queryset:
            if rescisao.confirmado_por_inquilino:
                continue
            
            locatario = rescisao.locacao.locatario
            telefone = locatario.telefone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
            if not telefone.startswith('55'):
                telefone = '55' + telefone
            
            link_confirmacao = f"{settings.SITE_URL}/rescisao/confirmar/{rescisao.token_confirmacao}/"
            
            mensagem = (
                f"RESCISAO DE CONTRATO\n\n"
    		f"Ola, {locatario.nome_razao_social}!\n\n"
    		f"Solicitamos a confirmacao da rescisao do contrato:\n"
    		f"Imovel: {rescisao.locacao.imovel.endereco}\n"
    		f"Data de desocupacao: {rescisao.data_desocupacao.strftime('%d/%m/%Y')}\n"
    		f"Valor total: R$ {rescisao.valor_total_devido:,.2f}\n\n"
    		f"Confirme atraves do link:\n{link_confirmacao}\n\n"
    		f"Duvidas? Entre em contato conosco!"
            )
            
            msg_encoded = urllib.parse.quote(mensagem)
            link_wa = "https://wa.me/" + str(telefone) + "?text=" + str(msg_encoded)
	    
            
            html += f"""
            <div style="margin:15px 0; padding:15px; background:#f5f5f5; border-left:4px solid #25D366;">
                <p><strong>Locatário:</strong> {locatario.nome_razao_social}<br>
                <strong>Contrato:</strong> {rescisao.locacao.numero_contrato}<br>
                <strong>Total:</strong> R$ {rescisao.valor_total_devido:,.2f}</p>
                <a href="{link_wa}" target="_blank" 
                   style="background:#25D366; color:white; padding:10px 20px; text-decoration:none; 
                          border-radius:5px; display:inline-block; font-weight:bold;">
                    Abrir WhatsApp ➜
                </a>
            </div>
            """
        
        html += '</div>'
        self.message_user(request, mark_safe(html), level='SUCCESS')
    
    @admin.action(description='🏁 Finalizar rescisão')
    def finalizar_rescisao(self, request, queryset):
        finalizados = 0
        
        for rescisao in queryset:
            if rescisao.saldo_devedor == 0:
                rescisao.status = 'FINALIZADA'
                rescisao.save()
                finalizados += 1
        
        self.message_user(request, f'✅ {finalizados} rescisão(ões) finalizada(s)!', level='SUCCESS')
