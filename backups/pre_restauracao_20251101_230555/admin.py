
from django.contrib import admin
from core.models import ConfiguracaoSistema, LogGeracaoComandas
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html
from .forms import PagamentoAdminForm
from .models import Fiador, Usuario, Locador, Imovel, Locatario, Locacao, Comanda, Pagamento, TemplateContrato, LogNotificacao
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime
from io import BytesIO
from .contrato_generator import gerar_contrato_pdf, gerar_contrato_docx


# ════════════════════════════════════════════════════════════
# USUARIO ADMIN - AUTENTICAÇÃO CORRIGIDA
# ════════════════════════════════════════════════════════════

class UsuarioCreationForm(UserCreationForm):
    """Form para criar novos usuários"""
    class Meta:
        model = Usuario
        fields = ('username', 'email', 'tipo_usuario')

class UsuarioChangeForm(UserChangeForm):
    """Form para editar usuários"""
    class Meta:
        model = Usuario
        fields = '__all__'

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin customizado para Usuario com autenticação correta"""
    
    form = UsuarioChangeForm
    add_form = UsuarioCreationForm
    
    list_display = ['username', 'email', 'tipo_usuario', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['tipo_usuario', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'cpf']
    
    fieldsets = (
        ('🔐 Autenticação', {
            'fields': ('username', 'password')
        }),
        ('👤 Dados Pessoais', {
            'fields': ('first_name', 'last_name', 'email', 'cpf', 'telefone', 'avatar')
        }),
        ('🎭 Perfil do Sistema', {
            'fields': ('tipo_usuario',)
        }),
        ('🔑 Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ['collapse'],
        }),
        ('📅 Datas Importantes', {
            'fields': ('date_joined', 'last_login'),
            'classes': ['collapse'],
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        ('👤 Informações', {
            'fields': ('first_name', 'last_name', 'tipo_usuario'),
        }),
        ('🔑 Permissões', {
            'fields': ('is_staff', 'is_active'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
    
    def save_model(self, request, obj, form, change):
        """Garante que usuários tenham acesso ao admin"""
        if not change:
            if not obj.is_staff:
                obj.is_staff = True
        super().save_model(request, obj, form, change)


# ════════════════════════════════════════════════════════════

from django.utils.html import format_html
from django.urls import reverse

@admin.register(Locador)
class LocadorAdmin(admin.ModelAdmin):
    """Admin organizado para Locador"""
    
    list_display = [
        'nome_razao_social',
        'representante',
        'tipo_locador',
        'cpf_cnpj',
        'telefone',
        'email',
        'is_active',
    ]
    
    list_filter = [
        'tipo_locador',
        'is_active',
        'created_at',
    ]
    
    search_fields = [
        'nome_razao_social',
        'representante',
        'cpf_cnpj',
        'email',
        'telefone',
    ]
    
    fieldsets = (
        ('📋 Dados Básicos', {
            'fields': (
                'usuario',
                'tipo_locador',
                'nome_razao_social',
                'representante',
                'cpf_cnpj',
            )
        }),
        ('📞 Contatos', {
            'fields': (
                'telefone',
                'email',
            )
        }),
        ('🏠 Endereço', {
            'fields': (
                'endereco_completo',
                'cep',
            )
        }),
        ('📝 Observações', {
            'fields': ('observacoes',),
            'classes': ['collapse'],
        }),
        ('🕐 Metadados', {
            'fields': (
                'created_at',
                'updated_at',
                'is_active',
            ),
            'classes': ['collapse'],
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
@admin.register(Imovel)
class ImovelAdmin(admin.ModelAdmin):
    """Admin organizado para Imóvel"""
    
    list_display = ['codigo_imovel', 'tipo_imovel', 'status', 'endereco', 'cidade', 'valor_aluguel', 'locador', 'is_active']
    list_filter = ['tipo_imovel', 'status', 'cidade', 'estado', 'is_active', 'created_at']
    search_fields = ['codigo_imovel', 'endereco', 'bairro', 'cidade', 'locador__nome_razao_social']
    
    fieldsets = (
        ('📋 Informações Básicas', {
            'fields': ('locador', 'codigo_imovel', 'tipo_imovel', 'status')
        }),
        ('📍 Endereço', {
            'fields': ('endereco', 'numero', 'bairro', 'cidade', 'estado', 'cep')
        }),
        ('📏 Características', {
            'fields': ('area_total', 'quartos', 'banheiros')
        }),
        ('💰 Valores', {
            'fields': ('valor_aluguel', 'valor_condominio')
        }),
        ('⚡ Utilidades / Contas', {
            'fields': ('conta_agua_esgoto', 'numero_hidrometro', 'unidade_consumidora_energia'),
            'description': 'Informações de contas de consumo do imóvel'
        }),
        ('📝 Descrição', {
            'fields': ('descricao',),
            'classes': ['collapse'],
        }),
        ('🕐 Metadados', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ['collapse'],
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']



@admin.register(Locatario)
class LocatarioAdmin(admin.ModelAdmin):
    """Admin organizado para Locatário"""
    
    list_display = ['nome_razao_social', 'cpf_cnpj', 'telefone', 'email', 'empresa_trabalho', 'tem_fiador', 'is_active']
    list_filter = ['created_at', 'is_active']
    search_fields = ['nome_razao_social', 'cpf_cnpj', 'rg', 'email', 'telefone', 'empresa_trabalho']
    
    fieldsets = (
        ('📋 Dados Pessoais', {
            'fields': ('nome_razao_social', 'cpf_cnpj', 'rg', 'data_nascimento')
        }),
        ('👨‍👩‍👦 Filiação', {
            'fields': ('nome_pai', 'nome_mae'),
            'classes': ['collapse'],
        }),
        ('📞 Contatos', {
            'fields': ('telefone', 'email', 'outro_telefone', ('nome_contato_emergencia', 'telefone_contato_emergencia'))
        }),
        ('🏠 Endereço', {
            'fields': ('endereco_completo',)
        }),
        ('💼 Dados Profissionais', {
            'fields': ('empresa_trabalho', 'endereco_empresa', 'telefone_empresa', 'contato_empresa', 'tempo_empresa', 'renda_mensal')
        }),
        ('🛡️ Garantia', {
            'fields': ('fiador',),
            'description': 'Selecione um fiador cadastrado ou deixe em branco se não houver'
        }),
        ('🕐 Metadados', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ['collapse'],
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    @admin.display(description='Fiador', boolean=True)
    def tem_fiador(self, obj):
        return obj.fiador is not None



@admin.register(Locacao)

class LocacaoAdmin(admin.ModelAdmin):
    """Admin atualizado com geração de contratos"""
    
    list_display = [
        'numero_contrato',
        'imovel',
        'locatario',
        'data_inicio',
        'data_fim',
        'valor_aluguel',
        'status',
        'acoes_contrato',
    ]
    
    list_filter = ['status', 'data_inicio']
    
    search_fields = [
        'numero_contrato',
        'imovel__codigo_imovel',
        'locatario__nome_razao_social',
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['gerar_contrato_pdf_action', 'gerar_contrato_docx_action']
    
    fieldsets = (
        ('📋 Informações Básicas', {
            'fields': (
                'numero_contrato',
                'imovel',
                'locatario',
                'status',
            ),
            'description': '⚠️ Deixe o número do contrato VAZIO para gerar automaticamente'
        }),
        ('📅 Datas', {
            'fields': (
                'data_inicio',
                'data_fim',
            )
        }),
        ('💰 Valores', {
            'fields': (
                'valor_aluguel',
                'dia_vencimento',
            )
        }),
        ('🕐 Metadados', {
            'fields': (
                'created_at',
                'updated_at',
                'is_active',
            ),
            'classes': ['collapse'],
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Remove required do numero_contrato"""
        form = super().get_form(request, obj, **kwargs)
        if 'numero_contrato' in form.base_fields:
            form.base_fields['numero_contrato'].required = False
            form.base_fields['numero_contrato'].help_text = '✨ Deixe vazio para gerar automaticamente'
        return form
    
    @admin.display(description='Contratos')
    def acoes_contrato(self, obj):
        """Botões para gerar contratos"""
        if obj.pk:
            return format_html(
                '<a class="button" href="/admin/locacao/{}/contrato/pdf/" target="_blank">📄 PDF</a> '
                '<a class="button" href="/admin/locacao/{}/contrato/docx/" target="_blank">📝 DOCX</a>',
                obj.pk, obj.pk
            )
        return '-'
    
    @admin.action(description='📄 Gerar Contrato PDF')
    def gerar_contrato_pdf_action(self, request, queryset):
        """Action para gerar PDF"""
        if queryset.count() == 1:
            return gerar_contrato_pdf(queryset.first())
        else:
            self.message_user(request, '❌ Selecione apenas UMA locação', level='error')
    
    @admin.action(description='📝 Gerar Contrato DOCX')
    def gerar_contrato_docx_action(self, request, queryset):
        """Action para gerar DOCX"""
        if queryset.count() == 1:
            return gerar_contrato_docx(queryset.first())
        else:
            self.message_user(request, '❌ Selecione apenas UMA locação', level='error')
    
    def save_model(self, request, obj, form, change):
        """Mostra número gerado"""
        super().save_model(request, obj, form, change)
        if not change:
            self.message_user(
                request,
                f'✅ Contrato criado: {obj.numero_contrato}',
                level='success'
            )
    
    actions = ['gerar_contrato']
    
    def gerar_contrato(self, request, queryset):
        """Gerar contratos em Word."""
        from .document_generator import DocumentGenerator
        generator = DocumentGenerator()
        
        contratos_gerados = []
        for locacao in queryset:
            try:
                filename = generator.gerar_contrato_locacao(locacao.id)
                contratos_gerados.append(filename)
            except Exception as e:
                self.message_user(request, f'Erro ao gerar contrato {locacao.numero_contrato}: {e}', level='ERROR')
        
        if contratos_gerados:
            self.message_user(request, f'{len(contratos_gerados)} contrato(s) gerado(s) com sucesso!')
    
    gerar_contrato.short_description = "Gerar contratos Word"
    list_display = ('numero_contrato', 'imovel', 'locatario', 'status', 'data_inicio', 'data_fim')
    list_filter = ('status', 'is_active', 'created_at')
    search_fields = ('numero_contrato', 'imovel__codigo_imovel', 'locatario__nome_razao_social')

    def get_form(self, request, obj=None, **kwargs):
        """Remove required do numero_contrato para permitir geração automática"""
        form = super().get_form(request, obj, **kwargs)
        if 'numero_contrato' in form.base_fields:
            form.base_fields['numero_contrato'].required = False
        return form

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Adiciona botões de gerar contrato."""
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj:
            from django.urls import reverse
            extra_context['show_contrato_buttons'] = True
            extra_context['contrato_docx_url'] = reverse('gerar_contrato_docx', args=[obj.pk])
            extra_context['contrato_pdf_url'] = reverse('gerar_contrato_pdf', args=[obj.pk])
        return super().change_view(request, object_id, form_url, extra_context)
"""
Admin melhorado para o modelo Comanda
Adicionar/substituir no arquivo: core/admin.py

Autor: SGLI System
Data: 06/10/2025
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from decimal import Decimal

from .models import Comanda, Pagamento


class PagamentoInline(admin.TabularInline):
    """Inline para ver/adicionar pagamentos direto na comanda"""
    model = Pagamento
    extra = 0
    fields = ['data_pagamento', 'valor_pago', 'forma_pagamento', 'status', 'comprovante']
    readonly_fields = ['numero_pagamento', 'created_at']
    
    def has_delete_permission(self, request, obj=None):
        # Permitir deletar apenas pagamentos pendentes
        if obj and obj.status == 'confirmado':
            return False
        return True


@admin.register(Comanda)
class ComandaAdmin(admin.ModelAdmin):
    """Admin melhorado para Comanda com organização por seções"""
    
    list_display = [
        'numero_comanda_link',
        'locacao_info',
        'mes_ano_referencia',
        'vencimento_colorido',
        'valor_total_formatado',
        'status_badge',
        'dias_vencimento',
        'painel_whatsapp_button',
    ]
    
    list_filter = [
        'status',
        'data_vencimento',
        'mes_referencia',
        'ano_referencia',
        'locacao__imovel__tipo_imovel',
    ]
    
    search_fields = [
        'numero_comanda',
        'locacao__numero_contrato',
        'locacao__locatario__nome_razao_social',
        'locacao__imovel__codigo_imovel',
        'locacao__imovel__endereco',
    ]
    
    readonly_fields = [
        'numero_comanda',
        'created_at',
        'updated_at',
        'valor_total_display',
        'valor_pendente_display',
        'dias_atraso_display',
    ]
    
    date_hierarchy = 'data_vencimento'
    
    inlines = [PagamentoInline]
    
    # Organizar campos em seções
    fieldsets = (
        ('📋 Informações Básicas', {
            'fields': (
                'numero_comanda',
                'locacao',
                ('mes_referencia', 'ano_referencia'),
                'status',
            )
        }),
        ('📅 Datas', {
            'fields': (
                'data_vencimento',
                'data_pagamento',
                'dias_atraso_display',
            )
        }),
        ('💰 Valores Base', {
            'fields': (
                'valor_aluguel',
                'valor_condominio',
                'valor_iptu',
                'valor_administracao',
            ),
            'description': 'Valores base calculados automaticamente na geração'
        }),
        ('➕ Valores Adicionais', {
            'fields': (
                'outros_debitos',
                'outros_creditos',
            ),
            'description': 'AQUI você adiciona despesas extras: água, luz, gás, reparos, etc.'
        }),
        ('⚖️ Ajustes Financeiros', {
            'fields': (
                'valor_multa',
                'valor_juros',
                'desconto',
            ),
            'classes': ['collapse'],
        }),
        ('💵 Totalizadores', {
            'fields': (
                'valor_total_display',
                'valor_pago',
                'valor_pendente_display',
            )
        }),
        ('💳 Pagamento', {
            'fields': (
                'forma_pagamento',
                'comprovante_pagamento',
            ),
            'classes': ['collapse'],
        }),
        ('🔔 Notificações', {
            'fields': (
                'notificacao_enviada_7dias',
                'notificacao_enviada_1dia',
                'notificacao_atraso_enviada',
            ),
            'classes': ['collapse'],
        }),
        ('📝 Observações', {
            'fields': ('observacoes',),
            'classes': ['collapse'],
        }),
        ('🕐 Metadados', {
            'fields': (
                'created_at',
                'updated_at',
                'is_active',
            ),
            'classes': ['collapse'],
        }),
    )
    
    actions = [
        'aplicar_multas_juros',
        'marcar_como_paga',
        'cancelar_comandas',
        'exportar_para_excel',
    ]
    
    # Métodos personalizados para list_display
    
    @admin.display(description='Número', ordering='numero_comanda')
    def numero_comanda_link(self, obj):
        url = reverse('admin:core_comanda_change', args=[obj.id])
        return format_html('<a href="{}" style="font-weight: bold; color: #667eea;">{}</a>', url, obj.numero_comanda)
    
    @admin.display(description='Locação')
    def locacao_info(self, obj):
        return format_html(
            '<strong>{}</strong><br>'
            '<small style="color: #666;">{}</small>',
            obj.locacao.locatario.nome_razao_social,
            obj.locacao.imovel.codigo_imovel
        )
    
    @admin.display(description='Mês/Ano', ordering='mes_referencia')
    def mes_ano_referencia(self, obj):
        return obj.mes_referencia.strftime('%m/%Y')
    
    @admin.display(description='Vencimento', ordering='data_vencimento')
    def vencimento_colorido(self, obj):
        from django.utils import timezone
        hoje = timezone.now().date()
        
        if obj.status == 'PAGA':
            cor = '#28a745'
            icone = '✓'
        elif obj.data_vencimento < hoje:
            cor = '#dc3545'
            icone = '⚠️'
        elif obj.data_vencimento == hoje:
            cor = '#ffc107'
            icone = '⏰'
        else:
            cor = '#17a2b8'
            icone = '📅'
        
        return format_html(
            '<span style="color: {};">{} {}</span>',
            cor,
            icone,
            obj.data_vencimento.strftime('%d/%m/%Y')
        )
    
    @admin.display(description='Valor Total', ordering='valor_aluguel')
    def valor_total_formatado(self, obj):
        valor = obj.valor_total
        cor = '#28a745' if obj.status == 'PAID' else '#333'
        return format_html(
            '<strong style="color: {}; font-size: 15px;">R$ {}</strong>',
            cor,
            f'{float(valor):,.2f}'
        )
    
    @admin.display(description='Status')
    def status_badge(self, obj):
        badges = {
            'PENDING': ('⏳', 'Pendente', '#ffc107', '#000'),
            'PAID': ('✅', 'Paga', '#28a745', '#fff'),
            'OVERDUE': ('❌', 'Vencida', '#dc3545', '#fff'),
            'PARTIAL': ('⚡', 'Parcial', '#17a2b8', '#fff'),
            'CANCELLED': ('🚫', 'Cancelada', '#6c757d', '#fff'),
        }
        
        icone, texto, bg, fg = badges.get(obj.status, ('?', obj.status, '#ccc', '#000'))
        
        return format_html(
            '<span style="background: {}; color: {}; padding: 4px 10px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">'
            '{} {}</span>',
            bg, fg, icone, texto
        )
    
    @admin.display(description='Atraso')
    def dias_vencimento(self, obj):
        if obj.status == 'PAID':
            return format_html('<span style="color: #28a745;">✓ Paga</span>')
        
        dias = obj.dias_atraso
        if dias == 0:
            return format_html('<span style="color: #17a2b8;">Em dia</span>')
        elif dias > 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">{} dia(s)</span>',
                dias
            )
        else:
            return format_html(
                '<span style="color: #666;">{} dia(s)</span>',
                abs(dias)
            )
    
    # Campos readonly personalizados
    
    @admin.display(description='💰 Valor Total')
    def valor_total_display(self, obj):
        return format_html(
            '<div style="font-size: 20px; font-weight: bold; color: #667eea; '
            'padding: 10px; background: #f0f4ff; border-radius: 8px; text-align: center;">'
            'R$ {:.2f}</div>',
            obj.valor_total
        )
    
    @admin.display(description='💵 Valor Pendente')
    def valor_pendente_display(self, obj):
        pendente = obj.valor_pendente
        cor = '#28a745' if pendente == 0 else '#dc3545'
        return format_html(
            '<div style="font-size: 18px; font-weight: bold; color: {}; '
            'padding: 10px; background: #f8f9fa; border-radius: 8px; text-align: center;">'
            'R$ {:.2f}</div>',
            cor,
            pendente
        )
    
    @admin.display(description='⏰ Dias de Atraso')
    def dias_atraso_display(self, obj):
        dias = obj.dias_atraso
        if dias == 0:
            return format_html('<span style="color: #28a745; font-size: 16px;">✓ Em dia</span>')
        elif dias > 0:
            return format_html(
                '<span style="color: #dc3545; font-size: 16px; font-weight: bold;">'
                '⚠️ {} dia(s) de atraso</span>',
                dias
            )
        else:
            return format_html(
                '<span style="color: #17a2b8; font-size: 16px;">'
                '📅 Vence em {} dia(s)</span>',
                abs(dias)
            )
    
    # Actions customizadas
    
    @admin.action(description='⚖️ Aplicar multas e juros')
    def aplicar_multas_juros(self, request, queryset):
        """Aplica multas e juros nas comandas vencidas selecionadas"""
        from django.utils import timezone
        
        comandas_vencidas = queryset.filter(
            data_vencimento__lt=timezone.now().date(),
            status__in=['PENDING', 'OVERDUE', 'PARTIAL']
        )
        
        atualizadas = 0
        for comanda in comandas_vencidas:
            comanda.aplicar_multa_juros(salvar=True)
            atualizadas += 1
        
        self.message_user(
            request,
            f'✅ Multas e juros aplicados em {atualizadas} comanda(s).',
            level='success'
        )
    
    @admin.action(description='✅ Marcar como pagas')
    def marcar_como_paga(self, request, queryset):
        """Marca comandas como pagas"""
        from django.utils import timezone
        
        atualizadas = 0
        for comanda in queryset:
            if comanda.status != 'PAID':
                comanda.valor_pago = comanda.valor_total
                comanda.data_pagamento = timezone.now().date()
                comanda.status = 'PAID'
                comanda.save()
                atualizadas += 1
        
        self.message_user(
            request,
            f'✅ {atualizadas} comanda(s) marcada(s) como pagas.',
            level='success'
        )
    
    @admin.action(description='🚫 Cancelar comandas')
    def cancelar_comandas(self, request, queryset):
        """Cancela as comandas selecionadas"""
        atualizadas = queryset.update(status='CANCELLED')
        
        self.message_user(
            request,
            f'🚫 {atualizadas} comanda(s) cancelada(s).',
            level='warning'
        )
    
    @admin.action(description='📊 Exportar para Excel')
    def exportar_para_excel(self, request, queryset):
        """Exporta comandas selecionadas para Excel"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="comandas.csv"'
        response.write('\ufeff'.encode('utf-8'))  # BOM para Excel reconhecer UTF-8
        
        writer = csv.writer(response, delimiter=';')
        writer.writerow([
            'Número',
            'Locação',
            'Locatário',
            'Imóvel',
            'Mês/Ano',
            'Vencimento',
            'Valor Aluguel',
            'Valor Condomínio',
            'Outros Débitos',
            'Outros Créditos',
            'Multa',
            'Juros',
            'Desconto',
            'Valor Total',
            'Valor Pago',
            'Valor Pendente',
            'Status',
        ])
        
        for comanda in queryset:
            writer.writerow([
                comanda.numero_comanda,
                comanda.locacao.numero_contrato,
                comanda.locacao.locatario.nome_razao_social,
                comanda.locacao.imovel.codigo_imovel,
                comanda.mes_referencia.strftime('%m/%Y'),
                comanda.data_vencimento.strftime('%d/%m/%Y'),
                str(comanda.valor_aluguel).replace('.', ','),
                str(comanda.valor_condominio).replace('.', ','),
                str(comanda.outros_debitos).replace('.', ','),
                str(comanda.outros_creditos).replace('.', ','),
                str(comanda.multa).replace('.', ','),
                str(comanda.juros).replace('.', ','),
                str(comanda.desconto).replace('.', ','),
                str(comanda.valor_total).replace('.', ','),
                str(comanda.valor_pago).replace('.', ','),
                str(comanda.valor_pendente).replace('.', ','),
                comanda.get_status_display(),
            ])
        
        self.message_user(
            request,
            f'📊 {queryset.count()} comanda(s) exportada(s) com sucesso.',
            level='success'
        )
        
        return response
    
    def get_queryset(self, request):
        """Otimiza queries com select_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'locacao',
            'locacao__locatario',
            'locacao__imovel',
            'locacao__imovel__locador'
        )
    
    def painel_whatsapp_button(self, obj):
        url = reverse('painel_whatsapp')
        return format_html(
            '<a class="button" href="{}">📲 Painel WhatsApp</a>', 
            url
        )
    painel_whatsapp_button.short_description = "Acesso Rápido"
    
    class Media:
        css = {
            'all': ('admin/css/comanda_custom.css',)
        }
        js = ('admin/js/comanda_custom.js',)


    # Registrar modelo de Log se ainda não estiver registrado
    from .models import LogGeracaoComandas

@admin.register(LogGeracaoComandas)
class LogGeracaoComandaAdmin(admin.ModelAdmin):
    """Admin para visualizar logs de geração de comandas"""
    
    list_display = [
        'data_execucao',
        'mes_referencia_formatado',
        'comandas_geradas',
        'comandas_duplicadas',
        'locacoes_processadas',
        'sucesso_badge',
        'executado_por',
    ]
    
    list_filter = [
        'sucesso',
        'executado_por',
        'mes_referencia',
        'data_execucao',
    ]
    
    readonly_fields = [
        'data_execucao',
        'mes_referencia',
        'comandas_geradas',
        'comandas_duplicadas',
        'locacoes_processadas',
        'sucesso',
        'mensagem',
        'erro',
        'executado_por',
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    @admin.display(description='Mês', ordering='mes_referencia')
    def mes_referencia_formatado(self, obj):
        return obj.mes_referencia.strftime('%B/%Y').capitalize()
    
    @admin.display(description='Sucesso')
    def sucesso_badge(self, obj):
        if obj.sucesso:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 4px 10px; '
                'border-radius: 12px; font-size: 12px; font-weight: bold;">✅ Sucesso</span>'
            )
        else:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 4px 10px; '
                'border-radius: 12px; font-size: 12px; font-weight: bold;">❌ Erro</span>'
            )

#@admin.register(Comanda)
#class ComandaAdmin(admin.ModelAdmin):
   # list_display = ('numero_comanda', 'locacao', 'mes_referencia', 'ano_referencia', 'status', 'data_vencimento')
   # list_filter = ('status', 'ano_referencia', 'mes_referencia', 'is_active')
   # search_fields = ('numero_comanda', 'locacao__numero_contrato', 'locacao__locatario__nome_razao_social')
   # readonly_fields = ('numero_comanda',)

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    form = PagamentoAdminForm
    
    actions = ['gerar_recibo']
    
    # ═══ CONFIGURAÇÃO DE EXIBIÇÃO ═══
    list_display = (
        'numero_pagamento',
        'comanda_link',
        'locatario_nome',
        'valor_pago_formatado',
        'data_pagamento',
        'forma_pagamento',
        'status_badge',
        'acoes_rapidas',
    )
    
    list_filter = (
        'status',
        'forma_pagamento',
        'data_pagamento',
    )
    
    search_fields = (
        'numero_pagamento',
        'comanda__numero_comanda',
        'comanda__locacao__locatario__nome_razao_social',
        'comanda__locacao__imovel__endereco',
    )
    
    readonly_fields = ('numero_pagamento', 'data_confirmacao', 'created_at', 'updated_at')
    
    date_hierarchy = 'data_pagamento'
    
    list_per_page = 25
    
    ordering = ('-data_pagamento',)
    
    # ═══ MÉTODOS CUSTOMIZADOS ═══
    

    @admin.display(description='Comanda', ordering='comanda__numero_comanda')
    def comanda_link(self, obj):
        """Link clicável para a comanda."""
        from django.urls import reverse
        from django.utils.html import format_html
        
        if obj.comanda:
            url = reverse('admin:core_comanda_change', args=[obj.comanda.id])
            return format_html(
                '<a href="{}" target="_blank" style="color: #3b82f6; font-weight: 600;">{}</a>',
                url,
                obj.comanda.numero_comanda
            )
        return '-'

    @admin.display(description='Locatário', ordering='comanda__locacao__locatario__nome_razao_social')
    def locatario_nome(self, obj):
        """Nome do locatário com link."""
        from django.urls import reverse
        from django.utils.html import format_html
        
        if obj.comanda and obj.comanda.locacao:
            locatario = obj.comanda.locacao.locatario
            url = reverse('admin:core_locatario_change', args=[locatario.id])
            return format_html(
                '<a href="{}" target="_blank" style="color: #3b82f6; font-weight: 600;">{}</a>',
                url,
                locatario.nome_razao_social
            )
        return '-'
    
    @admin.display(description='Valor Pago', ordering='valor_pago')
    def valor_pago_formatado(self, obj):
        """Valor formatado em Real."""
        from django.utils.html import format_html
        cor = '#27ae60' if obj.status == 'CONFIRMADO' else '#95a5a6'
        valor = f'{obj.valor_pago:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        return format_html(
            '<span style="color: {}; font-weight: 700;">R$ {}</span>',
            cor,
            valor
        )
    
    @admin.display(description='Status')
    def status_badge(self, obj):
        """Badge colorido para status."""
        from django.utils.html import format_html
        
        cores = {
            'PENDENTE': '#f39c12',
            'CONFIRMADO': '#27ae60',
            'CANCELADO': '#e74c3c',
            'ESTORNADO': '#95a5a6'
        }
        
        cor = cores.get(obj.status, '#95a5a6')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-size: 11px; font-weight: 700;">{}</span>',
            cor,
            obj.get_status_display()
        )
    

    @admin.display(description='Ações')
    def acoes_rapidas(self, obj):
        """Botões de ação rápida para cada pagamento."""
        from django.utils.html import format_html
        from django.urls import reverse
        
        recibo_url = reverse('pagina_recibo_pagamento', args=[obj.id])
        
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<a href="{}" class="button" style="padding: 5px 10px; background: #3b82f6; '
            'color: white; text-decoration: none; border-radius: 4px; font-size: 12px;" '
            'title="Baixar Recibo">🧾 Recibo</a>'
            '</div>',
            recibo_url
        )

    def gerar_recibo(self, request, queryset):
        """Gerar recibos em Word."""
        from .document_generator import DocumentGenerator
        generator = DocumentGenerator()
        
        recibos_gerados = []
        for pagamento in queryset:
            try:
                filename = generator.gerar_recibo_pagamento(pagamento.id)
                recibos_gerados.append(filename)
            except Exception as e:
                self.message_user(request, f'Erro ao gerar recibo {pagamento.numero_pagamento}: {e}', level='ERROR')
        
        if recibos_gerados:
            self.message_user(request, f'{len(recibos_gerados)} recibo(s) gerado(s) com sucesso!')
    
    gerar_recibo.short_description = "📄 Gerar recibos Word"
    
    def get_readonly_fields(self, request, obj=None):
        """Mostrar info_contrato apenas na edição."""
        if obj:
            return self.readonly_fields + ('info_contrato',) if hasattr(obj, 'info_contrato') else self.readonly_fields
        return self.readonly_fields


class TemplateContratoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'locador', 'tipo_imovel', 'is_default', 'created_at')
    list_filter = ('is_default', 'tipo_imovel', 'locador')
    search_fields = ('nome', 'descricao')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'arquivo_template')
        }),
        ('Associações', {
            'fields': ('locador', 'tipo_imovel', 'is_default'),
            'description': 'Defina quando este template deve ser usado'
        })
    )


# ========== ADMIN: CONFIGURAÇÃO DO SISTEMA ==========
@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Configurações de Comandas', {
            'fields': ('dia_vencimento_padrao', 'gerar_comandas_automaticamente')
        }),
        ('Metadados', {
            'fields': ('atualizado_em', 'atualizado_por'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('atualizado_em',)
    
    def has_add_permission(self, request):
        # Permitir apenas uma instância (Singleton)
        return not ConfiguracaoSistema.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


#@admin.register(LogGeracaoComandas)
class LogGeracaoComandasAdmin(admin.ModelAdmin):
    list_display = (
        'data_execucao', 
        'mes_referencia_display', 
        'comandas_geradas', 
        'comandas_duplicadas',
        'sucesso_display',
        'executado_por'
    )
    list_filter = ('sucesso', 'executado_por', 'data_execucao')
    search_fields = ('mensagem', 'erro')
    readonly_fields = (
        'data_execucao', 
        'mes_referencia', 
        'comandas_geradas',
        'comandas_duplicadas', 
        'locacoes_processadas',
        'sucesso', 
        'mensagem', 
        'erro', 
        'executado_por'
    )
    
    def mes_referencia_display(self, obj):
        return obj.mes_referencia.strftime('%B/%Y')
    mes_referencia_display.short_description = 'Mês'
    
    def sucesso_display(self, obj):
        if obj.sucesso:
            return '✅ Sucesso'
        return '❌ Erro'
    sucesso_display.short_description = 'Status'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ===========================================================================
# ADMIN FIADOR
# ===========================================================================

@admin.register(Fiador)
class FiadorAdmin(admin.ModelAdmin):
    """Admin para Fiador."""
    
    list_display = ['nome_completo', 'cpf', 'telefone', 'empresa_trabalho', 'created_at']
    list_filter = ['created_at', 'is_active']
    search_fields = ['nome_completo', 'cpf', 'rg', 'email', 'telefone']
    
    fieldsets = (
        ('📋 Dados Pessoais', {
            'fields': ('nome_completo', 'cpf', 'rg', 'data_nascimento')
        }),
        ('👨‍👩‍👦 Filiação', {
            'fields': ('nome_pai', 'nome_mae'),
            'classes': ['collapse'],
        }),
        ('📞 Contatos', {
            'fields': ('telefone', 'email', 'outro_telefone', ('nome_contato_emergencia', 'telefone_contato_emergencia'))
        }),
        ('🏠 Endereço', {
            'fields': ('endereco_completo', 'cep')
        }),
        ('💼 Dados Profissionais', {
            'fields': ('empresa_trabalho', 'endereco_empresa', 'telefone_empresa', 'contato_empresa', 'tempo_empresa', 'renda_mensal')
        }),
        ('🕐 Metadados', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ['collapse'],
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']



# ════════════════════════════════════════════
# ADMIN: NOTIFICAÇÕES
# ════════════════════════════════════════════
from core.notifications.models import NotificacaoLog

@admin.register(NotificacaoLog)
class NotificacaoLogAdmin(admin.ModelAdmin):
    """Admin para logs de notificações"""
    
    list_display = [
        'data_envio',
        'tipo',
        'destinatario',
        'status',
        'comanda_info',
    ]
    
    list_filter = ['tipo', 'status', 'data_envio']
    
    search_fields = [
        'destinatario',
        'comanda__locacao__locatario__nome_razao_social',
    ]
    
    readonly_fields = [
        'comanda',
        'tipo',
        'destinatario',
        'status',
        'mensagem',
        'data_envio',
    ]
    
    def comanda_info(self, obj):
        """Mostra informações da comanda"""
        return f"{obj.comanda.locacao.locatario.nome_razao_social} - {obj.comanda.mes_referencia.strftime('%m/%Y')}"
    comanda_info.short_description = 'Comanda'
    
    def has_add_permission(self, request):
        """Não permite adicionar logs manualmente"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Não permite deletar logs"""
        return False


@admin.register(LogNotificacao)
class LogNotificacaoAdmin(admin.ModelAdmin):
    list_display = ['comanda', 'tipo_notificacao', 'destinatario_email', 'enviado_em', 'sucesso']
    list_filter = ['tipo_notificacao', 'sucesso', 'enviado_em']
    search_fields = ['comanda__numero_comanda', 'destinatario_email']
    readonly_fields = ['enviado_em']
    date_hierarchy = 'enviado_em'

# Registro do TemplateContrato
admin.site.register(TemplateContrato, TemplateContratoAdmin)
