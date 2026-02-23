
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .dashboard_tokens import gerar_contexto_dashboard
from .admin_actions_tokens import (
    action_renovar_token_renovacao,
    action_reenviar_link_comanda,
    action_renovar_token_comanda,
    action_reenviar_link_recibo,
    action_renovar_token_recibo,
)
from django import forms
from core.models import ConfiguracaoSistema, LogGeracaoComandas
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .forms import PagamentoAdminForm
from .models import Fiador, Usuario, Locador, Imovel, Locatario, Locacao, Comanda, Pagamento, TemplateContrato
from core.views_comanda_web import gerar_token_comanda
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
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Q, F, Count
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.urls import reverse
from django.utils.html import format_html

class UsuarioCreationForm(UserCreationForm):
    """Form para criação de usuário com senha criptografada"""
    class Meta:
        model = Usuario
        fields = ('username', 'email', 'first_name', 'last_name', 'cpf', 'telefone', 'tipo_usuario')

class UsuarioChangeForm(UserChangeForm):
    """Form para edição de usuário"""
    class Meta:
        model = Usuario
        fields = '__all__'

@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Admin organizado para Usuario com senha criptografada"""
    
    # Forms corretos que criptografam senha
    add_form = UsuarioCreationForm
    form = UsuarioChangeForm
    
    list_display = ['username', 'get_full_name', 'email', 'tipo_usuario', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['tipo_usuario', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'cpf']
    
    # Fieldsets para ADICIONAR usuário (usa password1 e password2)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('👤 Dados Pessoais', {
            'fields': ('first_name', 'last_name', 'email', 'cpf', 'telefone', 'avatar')
        }),
        ('🎭 Perfil do Sistema', {
            'fields': ('tipo_usuario',)
        }),
    )
    
    # Fieldsets para EDITAR usuário (usa password widget especial)
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
    
    readonly_fields = ['date_joined', 'last_login']
    
    def save_model(self, request, obj, form, change):
        """
        Garante que senha é criptografada e flags são setadas corretamente.
        """
        # Se é novo usuário, a senha já vem criptografada do UserCreationForm
        # Apenas garantir flags corretas
        
        # Garantir is_active = True para novos usuários
        if not change:
            obj.is_active = True
        
        # Garantir is_staff = True para Admin e Gerente
        if obj.tipo_usuario in ['ADMIN', 'GERENTE']:
            obj.is_staff = True
        
        super().save_model(request, obj, form, change)
        
        # Mensagem de sucesso
        if not change:
            self.message_user(
                request,
                f'✅ Usuário {obj.username} criado com sucesso! '
                f'Tipo: {obj.get_tipo_usuario_display()}',
                level='success'
            )



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
        'alerta_vencimento',
        'acoes_contrato',
    ]
    
    list_filter = ['status', 'data_inicio']
    
    search_fields = [
        'numero_contrato',
        'imovel__codigo_imovel',
        'locatario__nome_razao_social',
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'numero_contrato', 'caucao_valor_total']
    
    actions = [
        'enviar_notificacao_renovacao_email',
        'enviar_notificacao_renovacao_whatsapp','gerar_contrato_pdf_action', 'gerar_contrato_docx_action']
    
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
        # ✅ NOVO DEV_20: Seção de Garantias
        ('🛡️ Garantias de Contrato', {
            'fields': (
                'tipo_garantia',
                'fiador_garantia',
                'caucao_quantidade_meses',
                'caucao_valor_total',
                'seguro_apolice',
                'seguro_seguradora',
            ),
            'description': '''
                <div style="background: #e3f2fd; padding: 10px; border-left: 4px solid #2196f3; margin-bottom: 10px;">
                    <strong>📌 Instruções:</strong><br>
                    1. Selecione o <strong>Tipo de Garantia</strong><br>
                    2. Preencha APENAS os campos correspondentes ao tipo selecionado<br>
                    3. Campos não preenchidos serão "NÃO INFORMADO" no contrato
                </div>
            ''',
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
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Remove required do numero_contrato e configura campos de garantia.
        ✅ NOVO DEV_20: Configurações dos campos de garantia
        """
        form = super().get_form(request, obj, **kwargs)
        
        # Configuração do numero_contrato (já existente)
        if 'numero_contrato' in form.base_fields:
            form.base_fields['numero_contrato'].required = False
            form.base_fields['numero_contrato'].help_text = '✨ Deixe vazio para gerar automaticamente'
        
        # ✅ NOVO DEV_20: Configurações dos campos de garantia
        if 'fiador_garantia' in form.base_fields:
            form.base_fields['fiador_garantia'].required = False
            form.base_fields['fiador_garantia'].help_text = '✅ Necessário apenas se Tipo = Fiador'
        
        if 'caucao_quantidade_meses' in form.base_fields:
            form.base_fields['caucao_quantidade_meses'].required = False
            form.base_fields['caucao_quantidade_meses'].help_text = '✅ Necessário apenas se Tipo = Caução'
        
        if 'caucao_valor_total' in form.base_fields:
            form.base_fields['caucao_valor_total'].required = False
            form.base_fields['caucao_valor_total'].help_text = '🔄 Calculado automaticamente'
        
        if 'seguro_apolice' in form.base_fields:
            form.base_fields['seguro_apolice'].required = False
            form.base_fields['seguro_apolice'].help_text = '✅ Necessário apenas se Tipo = Seguro'
        
        if 'seguro_seguradora' in form.base_fields:
            form.base_fields['seguro_seguradora'].required = False
            form.base_fields['seguro_seguradora'].help_text = '✅ Nome da seguradora'
        
        return form
    
    # ✅ NOVO DEV_20: Incluir JavaScript customizado
    class Media:
        js = ('admin/js/garantias_dinamicas.js',)

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
    
    
    @admin.display(description='⚠️ Alerta', ordering='data_fim')
    def alerta_vencimento(self, obj):
        """Exibe alerta para contratos vencendo em até 90 dias"""
        from django.utils import timezone
        from django.utils.html import format_html
        
        if not obj.data_fim:
            return '-'
        
        hoje = timezone.now().date()
        dias_restantes = (obj.data_fim - hoje).days
        
        if 0 <= dias_restantes <= settings.PRAZO_ALERTA_VENCIMENTO_DIAS:
            if dias_restantes <= 7:
                cor, icon = '#dc3545', '🚨'
            elif dias_restantes <= 30:
                cor, icon = '#fd7e14', '⚠️'
            else:
                cor, icon = '#ffc107', '⏰'
            
            return format_html(
                '<span style="color: {}; font-weight: bold; background: {}20; '
                'padding: 4px 10px; border-radius: 12px; font-size: 12px;">'
                '{} {} dia(s)</span>',
                cor, cor, icon, dias_restantes
            )
        elif dias_restantes < 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold; background: #dc354520; '
                'padding: 4px 10px; border-radius: 12px; font-size: 12px;">'
                '❌ Vencido há {} dia(s)</span>',
                abs(dias_restantes)
            )
        else:
            return format_html('<span style="color: #28a745;">✅ OK</span>')

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
    list_display = ('numero_contrato', 'imovel', 'locatario', 'status', 'data_inicio', 'data_fim', 'alerta_vencimento')
    list_filter = ('status', 'is_active', 'created_at')
    search_fields = ('numero_contrato', 'imovel__codigo_imovel', 'locatario__nome_razao_social')

"""
Admin melhorado para o modelo Comanda
Adicionar/substituir no arquivo: core/admin.py

Autor: SGLI System
Data: 06/10/2025
"""

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .dashboard_tokens import gerar_contexto_dashboard
from .admin_actions_tokens import (
    action_renovar_token_renovacao,
    action_reenviar_link_comanda,
    action_renovar_token_comanda,
    action_reenviar_link_recibo,
    action_renovar_token_recibo,
)
from django.utils.html import format_html
from django.db.models import Sum, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from decimal import Decimal

from .models import Comanda, Pagamento
from core.views_comanda_web import gerar_token_comanda


class PagamentoInline(GenericTabularInline):
    """Inline para ver/adicionar pagamentos direto na comanda"""
    model = Pagamento
    ct_field = "content_type"
    ct_fk_field = "object_id"
    extra = 0
    fields = ['data_pagamento', 'valor_pago', 'forma_pagamento', 'status', 'comprovante']
    readonly_fields = ['numero_pagamento', 'created_at']
    
    def has_delete_permission(self, request, obj=None):
        # Permitir deletar apenas pagamentos pendentes
        if obj and obj.status == 'confirmado':
            return False
        return True


class SaldoFilter(admin.SimpleListFilter):
    """Filtro customizado para saldo da comanda"""
    title = 'Saldo'
    parameter_name = 'saldo'
    
    def lookups(self, request, model_admin):
        return (
            ('positivo', 'Cliente tem crédito (Saldo +)'),
            ('zero', 'Conta quite (Saldo = 0)'),
            ('negativo', 'Cliente deve (Saldo -)'),
            ('alto_positivo', 'Crédito alto (> R$ 500)'),
            ('alto_negativo', 'Débito alto (< -R$ 500)'),
        )
    
    def queryset(self, request, queryset):
        """
        NOTA: Como valor_total é @property e não campo DB,
        filtramos em Python em vez de SQL.
        """
        from decimal import Decimal
        
        if not self.value():
            return queryset
        
        # Buscar todas as comandas e filtrar em Python
        comandas_filtradas = []
        
        for comanda in queryset:
            try:
                saldo = comanda.get_saldo()  # Usa método que calcula correto
                
                if self.value() == 'positivo' and saldo > 0:
                    comandas_filtradas.append(comanda.pk)
                elif self.value() == 'zero' and saldo == 0:
                    comandas_filtradas.append(comanda.pk)
                elif self.value() == 'negativo' and saldo < 0:
                    comandas_filtradas.append(comanda.pk)
                elif self.value() == 'alto_positivo' and saldo > Decimal('500.00'):
                    comandas_filtradas.append(comanda.pk)
                elif self.value() == 'alto_negativo' and saldo < Decimal('-500.00'):
                    comandas_filtradas.append(comanda.pk)
            except Exception:
                # Se erro ao calcular saldo, pular
                continue
        
        # Retornar queryset filtrado
        return queryset.filter(pk__in=comandas_filtradas)


@admin.register(Comanda)
class ComandaAdmin(admin.ModelAdmin):
    actions = [
        action_reenviar_link_comanda,
        action_renovar_token_comanda,
    ]
    """Admin melhorado para Comanda com organização por seções"""
    
    # ✅ Form customizado para excluir property valor_aluguel
    class ComandaAdminForm(forms.ModelForm):
        class Meta:
            model = Comanda
            fields = '__all__'
            # Excluir property valor_aluguel do formulário
            exclude = []
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Se for nova comanda, preencher _valor_aluguel_historico com valor do contrato
            if not self.instance.pk and 'locacao' in self.initial:
                try:
                    locacao = Locacao.objects.get(pk=self.initial['locacao'])
                    self.initial['_valor_aluguel_historico'] = locacao.valor_aluguel
                except Locacao.DoesNotExist:
                    pass
        
        def save(self, commit=True):
            """
            Garante que _valor_aluguel_historico seja preenchido antes de salvar.
            """
            from decimal import Decimal
            
            instance = super().save(commit=False)
            
            # Se for nova comanda e campo estiver vazio, preencher com valor do contrato
            if not instance.pk or instance._valor_aluguel_historico is None:
                if instance.locacao:
                    instance._valor_aluguel_historico = instance.locacao.valor_aluguel
                else:
                    instance._valor_aluguel_historico = Decimal('0.00')
            
            if commit:
                instance.save()
            
            return instance
    
    form = ComandaAdminForm


    @admin.display(description='💰 Aluguel')
    def valor_aluguel_display(self, obj):
        """Exibe valor do aluguel com indicador se é dinâmico ou histórico."""
        from django.utils.html import format_html
        from decimal import Decimal

        # 1. Usa a property inteligente do modelo Comanda
        valor_numerico = obj.valor_aluguel

        # 2. Garante que o valor é um tipo numérico
        try:
            valor_para_formatar = Decimal(str(valor_numerico))
        except (ValueError, TypeError):
            valor_para_formatar = Decimal('0.00')

        # 3. Determina o ícone e a cor baseado no status
        if obj.status in ['PENDING', 'OVERDUE']:
            icone = '🔄'
            cor = '#2563eb'
            estilo = 'font-weight: 600;'
        else:
            icone = '📌'
            cor = '#374151'
            estilo = 'font-weight: 500;'

        # 4. Formata a string de forma segura (formato brasileiro)
        valor_br = f"R$ {valor_para_formatar:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        return format_html(
            '<span style="color: {}; {}">{}</span> <span style="font-size: 10px; color: #6b7280;">{}</span>',
            cor,
            estilo,
            valor_br,
            icone
        )

    list_display = [
        'numero_comanda_link',
        'locacao_info',
        'mes_ano_referencia',
        'vencimento_colorido',
        'valor_aluguel_display',  # ← Mostra aluguel com indicador 🔄/📌
        'valor_total_formatado',
        'saldo_display',
        'acoes_envio',
        'status_badge',
        'dias_vencimento',
        ]
    
    list_filter = [
        'status',
        SaldoFilter,
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
        '_valor_aluguel_historico',
        'valor_aluguel_display',  # ← Campo histórico (readonly)
        'created_at',
        'updated_at',
        'valor_total_display',
        'saldo_display',
        'dias_atraso_display',
    ]
    
    date_hierarchy = 'data_vencimento'
    
    inlines = [PagamentoInline]
    
    def save_formset(self, request, form, formset, change):
        """
        Preenche usuario_registro_id com PK do usuário.
        Versão 5/5: robusta, com validação e debug.
        """
        instances = formset.save(commit=False)

        # Validar usuário autenticado
        if not getattr(request.user, "is_authenticated", False):
            raise ValueError("❌ Usuário não autenticado")
        
        user_pk = getattr(request.user, "pk", None)
        if not user_pk:
            raise ValueError("❌ Usuário sem PK")

        for instance in instances:
            # Atribuir PK diretamente ao campo FK
            if hasattr(instance, "usuario_registro_id"):
                if not getattr(instance, "usuario_registro_id", None):
                    instance.usuario_registro_id = user_pk

            # Limpar GenericFK se pagamento já tem comanda_id (aluguel)
            # Evita que GenericTabularInline preencha content_type indevidamente
            if getattr(instance, 'comanda_id', None):
                instance.content_type = None
                instance.object_id = None

            # Salvar instância
            instance.save()
                    
        # Salvar M2M
        formset.save_m2m()
        
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
                'valor_aluguel_display',  # ← Sincroniza: atual (PENDING) ou histórico (PAID)
                'valor_condominio',
                'valor_iptu',
                'valor_administracao',
            ),
            'description': '🔄 Aluguel sincroniza com contrato se PENDENTE | 📌 Congela se PAGO'
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
                'saldo_display',
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
        action_reenviar_link_comanda,
        action_renovar_token_comanda,
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
    
    def _get_dias_atraso_seguro(self, obj):
        """
        Método auxiliar para obter dias_atraso de forma segura.
        Protege contra problemas de cache do Python.
        """
        try:
            # Tentar acessar como property
            attr = getattr(obj, 'dias_atraso', None)
            
            # Se for callable (método), chamar
            if callable(attr):
                return attr()
            
            # Se for valor direto, retornar
            if attr is not None:
                return attr
            
            # Fallback: calcular manualmente
            if obj.data_vencimento and obj.status not in ['PAID', 'PAGA']:
                from django.utils import timezone
                dias = (timezone.now().date() - obj.data_vencimento).days
                return max(0, dias)
            
            return 0
        except Exception:
            return 0
    
    def _get_property_seguro(self, obj, property_name, default=0):
        """
        Método auxiliar genérico para obter @property de forma segura.
        Protege contra problemas de cache do Python com properties.
        
        Args:
            obj: Objeto do modelo
            property_name: Nome da property
            default: Valor padrão se falhar
        """
        try:
            attr = getattr(obj, property_name, None)
            
            # Se for callable (método), chamar
            if callable(attr):
                return attr()
            
            # Se for valor direto, retornar
            if attr is not None:
                return attr
            
            return default
        except Exception:
            return default
    
    @admin.display(description='Atraso')
    def dias_vencimento(self, obj):
        if obj.status == 'PAID':
            return format_html('<span style="color: #28a745;">✓ Paga</span>')
        
        dias = self._get_dias_atraso_seguro(obj)  # ← USO SEGURO
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
    

    @admin.display(description='📤 Ações')
    def acoes_envio(self, obj):
        """Botões para enviar comanda com mensagem WhatsApp detalhada e status inteligente"""
        from django.utils.html import format_html
        import urllib.parse
        from decimal import Decimal
        from django.conf import settings
        
        # 🔗 GERAR URL COMPLETA DA COMANDA - LÓGICA MELHORADA
        domain = None
        
        # 1. Tentar SITE_URL (variável de ambiente recomendada)
        domain = getattr(settings, 'SITE_URL', None)
        
        # 2. Se não tiver, buscar domínio Railway nos ALLOWED_HOSTS
        if not domain and hasattr(settings, 'ALLOWED_HOSTS'):
            for host in settings.ALLOWED_HOSTS:
                if 'railway.app' in host and host != '*':
                    domain = f"https://{host}"
                    break
        
        # 3. Fallback: primeiro host válido (não * ou localhost)
        if not domain and hasattr(settings, 'ALLOWED_HOSTS'):
            for host in settings.ALLOWED_HOSTS:
                if host not in ['*', 'localhost', '127.0.0.1', '.localhost']:
                    # Assumir HTTPS para hosts públicos
                    domain = f"https://{host}" if not host.startswith('http') else host
                    break
        
        # 4. Último recurso: desenvolvimento local
        if not domain:
            domain = "http://127.0.0.1:8000"
        
        token = gerar_token_comanda(str(obj.id))
        comanda_url = f"{domain}/comanda/{obj.id}/{token}/"
        
        loc = obj.locacao.locatario
        imovel = obj.locacao.imovel
        tel = ''.join(filter(str.isdigit, loc.telefone or ''))
        if tel and not tel.startswith('55'):
            tel = '55' + tel
        
        # ✅ LÓGICA INTELIGENTE DE STATUS
        status_comanda = obj.status
        saldo = obj.get_saldo() if hasattr(obj, 'get_saldo') else (obj.valor_pago - obj.valor_total)
        
        # Determinar observação baseada no status
        if status_comanda in ['PAID', 'PAGA']:
            if saldo > 0:
                obs_status = f'''

━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ *STATUS*
━━━━━━━━━━━━━━━━━━━━━━━━━━
Comanda QUITADA
Crédito de *R$ {abs(saldo):,.2f}* para o locatário'''
            else:
                obs_status = '''

━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ *STATUS*
━━━━━━━━━━━━━━━━━━━━━━━━━━
Comanda PAGA'''
        elif status_comanda == 'PARTIAL':
            saldo_restante = abs(saldo) if saldo < 0 else obj.valor_total - obj.valor_pago
            obs_status = f'''

━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ *STATUS*
━━━━━━━━━━━━━━━━━━━━━━━━━━
Pagamento PARCIAL efetuado
Saldo restante: *R$ {saldo_restante:,.2f}*'''
        elif status_comanda == 'OVERDUE':
            from django.utils import timezone
            dias = (timezone.now().date() - obj.data_vencimento).days
            obs_status = f'''

━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ *STATUS*
━━━━━━━━━━━━━━━━━━━━━━━━━━
Comanda VENCIDA há {dias} dia(s)'''
        else:
            obs_status = '''

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏳ *STATUS*
━━━━━━━━━━━━━━━━━━━━━━━━━━
Comanda PENDENTE de pagamento'''
        
        # ✅ MENSAGEM WHATSAPP COM DETALHAMENTO COMPLETO E AVISO
        msg = f'''📋 *COMANDA DE PAGAMENTO*

Olá *{loc.nome_razao_social}*!

━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 *VALORES DA COMANDA*
━━━━━━━━━━━━━━━━━━━━━━━━━━

Comanda: *{obj.numero_comanda}*
Vencimento: *{obj.data_vencimento.strftime('%d/%m/%Y')}*

DETALHAMENTO:
  • Aluguel: R$ {obj.valor_aluguel:,.2f}
  • Condomínio: R$ {obj.valor_condominio:,.2f}
  • IPTU: R$ {obj.valor_iptu:,.2f}'''

        # Adicionar multa/juros se houver
        if obj.valor_multa > 0 or obj.valor_juros > 0:
            msg += f'''
  • Multa (10%): R$ {obj.valor_multa:,.2f}
  • Juros (1% a.m.): R$ {obj.valor_juros:,.2f}'''

        # Adicionar outros débitos/créditos se houver
        if obj.outros_debitos > 0:
            msg += f'''
  • Outras despesas: R$ {obj.outros_debitos:,.2f}'''
        
        if obj.outros_creditos > 0:
            msg += f'''
  • Créditos: R$ -{obj.outros_creditos:,.2f}'''

        msg += f'''

TOTAL: *R$ {obj.valor_total:,.2f}*
{obs_status}

━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 *IMÓVEL*
━━━━━━━━━━━━━━━━━━━━━━━━━━
{imovel.endereco}, {imovel.numero}'''

        # 📝 OBSERVAÇÕES (se existirem)
        if hasattr(obj, 'observacoes') and obj.observacoes and obj.observacoes.strip():
            msg += f'''

━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 *COMENTÁRIOS*
━━━━━━━━━━━━━━━━━━━━━━━━━━
{obj.observacoes.strip()}'''

        msg += f'''

━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ *IMPORTANTE*
Pague seus débitos em dia e evite multas, juros e outras correções conforme contrato de locação.

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 *VER COMANDA COMPLETA*
━━━━━━━━━━━━━━━━━━━━━━━━━━
{comanda_url}

_Documento gerado via HABITAT PRO v1.0_'''

        wa_url = f'https://wa.me/{tel}?text={urllib.parse.quote(msg)}'
        
        return format_html(
            '<a href="{}" target="_blank" style="background:#25D366;color:white;padding:6px 12px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:11px;">💬 WhatsApp</a> '
            '<a href="/comanda/{}/enviar-email/" style="background:#3b82f6;color:white;padding:6px 12px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:11px;">📧 Email</a> '
            '<a href="{}" target="_blank" style="background:#8b5cf6;color:white;padding:6px 12px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:11px;">👁️ Ver</a>',
            wa_url, obj.id, comanda_url
        )
    
    def saldo_display(self, obj):
        """Exibe saldo com formatação, cor e destaque visual para valores altos"""
        from decimal import Decimal
        
        saldo = obj.get_saldo()
        saldo_fmt = obj.get_saldo_formatado()
        
        # Definir cor e ícone
        if saldo == 0:
            color = '#666'  # Cinza
            icon = '●'
            bg_color = '#f8f9fa'
        elif saldo > 0:
            color = '#28a745'  # Verde
            icon = '▲'
            bg_color = '#d4edda'
        else:
            color = '#dc3545'  # Vermelho
            icon = '▼'
            bg_color = '#f8d7da'
        
        # Destaque especial para valores altos (> R$ 500 ou < -R$ 500)
        if abs(saldo) > Decimal('500.00'):
            return format_html(
                '<span style="color: {}; font-weight: bold; font-size: 1.1em; '
                'background: {}; padding: 4px 8px; border-radius: 4px; '
                'border: 2px solid {}; display: inline-block;">'
                '{} {}</span>',
                color, bg_color, color, icon, saldo_fmt
            )
        else:
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} {}</span>',
                color, icon, saldo_fmt
            )
    
    saldo_display.short_description = '💰 Saldo'
    saldo_display.admin_order_field = 'valor_pago'
    
    # Campos readonly personalizados
    
    @admin.display(description='💰 Valor Total')
    def valor_total_display(self, obj):
        """Exibe valor total formatado"""
        try:
            # Chamar property diretamente (não usar _get_property_seguro)
            valor = obj.valor_total
        
            if valor is None or valor <= 0:
                return '-'
        
            # Formatar para padrão brasileiro
            valor_formatado = f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        
            return format_html(
                '<div style="font-size: 20px; font-weight: bold; color: #667eea; '
                'padding: 10px; background: #f0f4ff; border-radius: 8px; text-align: center;">'
                'R$ {}</div>',
                valor_formatado
            )
        except Exception as e:
            return '-'
          
    
    @admin.display(description='⏰ Dias de Atraso')
    def dias_atraso_display(self, obj):
        dias = self._get_dias_atraso_seguro(obj)  # ← USO SEGURO
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
                str(comanda.valor_multa).replace('.', ','),  # ✅ CORRIGIDO
                str(comanda.valor_juros).replace('.', ','),  # ✅ CORRIGIDO
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
    actions = [
        action_reenviar_link_comanda,
        action_renovar_token_comanda,
    ]
   # list_display = ('numero_comanda', 'locacao', 'mes_referencia', 'ano_referencia', 'status', 'data_vencimento')
   # list_filter = ('status', 'ano_referencia', 'mes_referencia', 'is_active')
   # search_fields = ('numero_comanda', 'locacao__numero_contrato', 'locacao__locatario__nome_razao_social')
   # readonly_fields = ('numero_comanda',)

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    form = PagamentoAdminForm
    
    actions = [
        action_reenviar_link_recibo,
        action_renovar_token_recibo,
        'gerar_recibo',
    ]
    
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
    
    gerar_recibo.short_description = "Gerar recibos Word"
    list_display = ('numero_pagamento', 'tipo_pagamento', 'locatario_nome', 'valor_pago', 'data_pagamento_br', 'forma_pagamento', 'status', 'botao_recibo')
    list_filter = ('status', 'forma_pagamento', 'data_pagamento')
    search_fields = ('numero_pagamento', 'comanda__numero_comanda', 'comanda__locacao__locatario__nome_razao_social')
    readonly_fields = ('numero_pagamento', 'data_confirmacao', 'created_at', 'updated_at')
    
    def get_readonly_fields(self, request, obj=None):
        """Mostrar info_contrato apenas na edição."""
        if obj:  # Editando
            return self.readonly_fields + ('info_contrato',)
        return self.readonly_fields  # Adicionando
    
    fieldsets = (
        ('Informações do Pagamento', {
            'fields': ('comanda', 'numero_pagamento', 'valor_pago', 'data_pagamento')
        }),
        ('Forma e Status', {
            'fields': ('forma_pagamento', 'status', 'data_confirmacao')
        }),
        ('Documentação', {
            'fields': ('comprovante', 'observacoes')
        }),
        ('Auditoria', {
            'fields': ('usuario_registro', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def tipo_pagamento(self, obj):
        """Identifica se o pagamento é de aluguel ou rescisão."""
        from django.utils.html import format_html
        if obj.comanda_id:
            return format_html(
                '<span style="background:#d1ecf1;color:#0c5460;padding:2px 8px;'
                'border-radius:4px;font-size:11px;font-weight:bold;">🏠 ALUGUEL</span>'
            )
        elif obj.content_type_id:
            return format_html(
                '<span style="background:#f8d7da;color:#721c24;padding:2px 8px;'
                'border-radius:4px;font-size:11px;font-weight:bold;">📄 RESCISÃO</span>'
            )
        return '—'
    tipo_pagamento.short_description = 'Tipo'

    def locatario_nome(self, obj):
        """
        Retorna nome do locatário independente do tipo de pagamento.
        Aluguel: via FK comanda → locacao → locatario
        Rescisão: via GenericFK comanda_ref → rescisao → locacao → locatario
        """
        try:
            # CASO 1: Pagamento de aluguel
            if obj.comanda_id:
                return obj.comanda.locacao.locatario.nome_razao_social
            # CASO 2: Pagamento de rescisão
            if obj.content_type_id and obj.object_id:
                ref = obj.comanda_ref
                if ref and hasattr(ref, 'rescisao'):
                    return ref.rescisao.locacao.locatario.nome_razao_social
            return '—'
        except Exception:
            return '—'
    locatario_nome.short_description = 'Locatário'

    def data_pagamento_br(self, obj):
        """Data no padrão brasileiro dd/mm/aaaa."""
        if obj.data_pagamento:
            return obj.data_pagamento.strftime('%d/%m/%Y')
        return '—'
    data_pagamento_br.short_description = 'Data'
    data_pagamento_br.admin_order_field = 'data_pagamento'

    @admin.display(description='🧾 Recibo')
    def botao_recibo(self, obj):
        """Botão para visualizar/enviar recibo"""
        from django.utils.html import format_html
        from django.urls import reverse
        
        if obj.status == 'confirmado':
            url = reverse('pagina_recibo_pagamento', kwargs={'pagamento_id': obj.id})
            return format_html(
                '<a href="{}" target="_blank" style="'
                'display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
                'color: white; padding: 6px 14px; border-radius: 6px; text-decoration: none; '
                'font-weight: bold; font-size: 12px;">🧾 Recibo</a>',
                url
            )
        return format_html('<span style="color: #999; font-size: 11px;">⏳ Aguardando</span>')
    

    
    def info_contrato(self, obj):
        """
        Exibe informações do contrato vinculado.
        Suporta Comanda (aluguel) e ComandaRescisao (rescisão).
        """
        from django.utils.html import format_html
        from django.urls import reverse

        try:
            # ── CASO 1: Pagamento de aluguel ──────────────────────
            if obj.comanda_id:
                locacao   = obj.comanda.locacao
                locatario = locacao.locatario
                imovel    = locacao.imovel
                url_locacao   = reverse('admin:core_locacao_change', args=[locacao.id])
                url_locatario = reverse('admin:core_locatario_change', args=[locatario.id])
                return format_html(
                    '<div style="padding:10px;background:#f8f9fa;border-radius:5px;">'
                    '🏠 <strong>ALUGUEL</strong><br>'
                    '<strong>Contrato:</strong> <a href="{}" target="_blank" style="color:#007bff;">{}</a><br>'
                    '<strong>Locatário:</strong> <a href="{}" target="_blank" style="color:#007bff;">{}</a><br>'
                    '<strong>Imóvel:</strong> {}<br>'
                    '<strong>Valor Aluguel:</strong> R$ {:.2f}'
                    '</div>',
                    url_locacao, locacao.numero_contrato,
                    url_locatario, locatario.nome_razao_social,
                    imovel.endereco_completo, locacao.valor_aluguel
                )

            # ── CASO 2: Pagamento de rescisão ─────────────────────
            if obj.content_type_id and obj.object_id:
                ref = obj.comanda_ref
                if ref and hasattr(ref, 'rescisao'):
                    rescisao  = ref.rescisao
                    locacao   = rescisao.locacao
                    locatario = locacao.locatario
                    imovel    = locacao.imovel
                    url_locacao   = reverse('admin:core_locacao_change', args=[locacao.id])
                    url_locatario = reverse('admin:core_locatario_change', args=[locatario.id])
                    return format_html(
                        '<div style="padding:10px;background:#fff3f3;border-radius:5px;">'
                        '📄 <strong>RESCISÃO</strong><br>'
                        '<strong>Contrato:</strong> <a href="{}" target="_blank" style="color:#007bff;">{}</a><br>'
                        '<strong>Locatário:</strong> <a href="{}" target="_blank" style="color:#007bff;">{}</a><br>'
                        '<strong>Imóvel:</strong> {}<br>'
                        '<strong>Parcela:</strong> {}ª de {} | R$ {:.2f}'
                        '</div>',
                        url_locacao, locacao.numero_contrato,
                        url_locatario, locatario.nome_razao_social,
                        imovel.endereco_completo,
                        ref.numero_parcela,
                        rescisao.quantidade_parcelas,
                        float(ref.valor)
                    )

        except Exception as e:
            return format_html(
                '<span style="color:#999;font-size:11px;">⚠️ Erro ao carregar: {}</span>',
                str(e)
            )

        return '—'
    info_contrato.short_description = 'Informações do Contrato'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_registro = request.user
        super().save_model(request, obj, form, change)


@admin.register(TemplateContrato)
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
    
    list_display = ['nome_completo', 'cpf', 'telefone', 'empresa_trabalho', 'created_at',
        ]
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

# Override Dashboard
from .dashboard_views import admin_index
# admin.site.index = admin_index  # COMENTADO - Dashboard isolado


# ════════════════════════════════════════════════════════════════════════════
# ADMIN DE RENOVAÇÃO DE CONTRATOS - DEV_21
# ════════════════════════════════════════════════════════════════════════════

from django.utils.html import format_html
from django.urls import reverse
from core.models import RenovacaoContrato
from core.services.whatsapp_service import WhatsAppService
from django.conf import settings


@admin.register(RenovacaoContrato)
class RenovacaoContratoAdmin(admin.ModelAdmin):
    """
    Admin para gerenciar renovações de contratos.
    Permite 3 canais de comunicação: Email, WhatsApp e Manual.
    """
    
    list_display = [
        'numero_contrato_original',
        'imovel_info',
        'locatario_info',
        'vencimento_info',
        'status_badge',
        'acoes_rapidas',
    ]
    
    list_filter = [
        'status',
        'data_proposta',
        'proprietario_aprovou',
        'locatario_aprovou',
    ]
    
    search_fields = [
        'locacao_original__numero_contrato',
        'locacao_original__imovel__endereco',
        'locacao_original__locatario__nome_razao_social',
    ]
    
    readonly_fields = [
        'data_proposta',
        'token_proprietario',
        'token_locatario',
        'data_aprovacao_proprietario',
        'ip_aprovacao_proprietario',
        'data_aprovacao_locatario',
        'ip_aprovacao_locatario',
        'exibir_ferramentas_comunicacao',
        'exibir_resumo_proposta',
    ]
    
    fieldsets = (
        ('Contrato Original', {
            'fields': ('locacao_original',)
        }),
        
        ('Proposta de Renovação', {
            'fields': (
                'exibir_resumo_proposta',
                'nova_data_inicio',
                'nova_data_fim',
                'nova_duracao_meses',
                'novo_valor_aluguel',
            ),
        }),
        
        ('Garantias', {
            'fields': (
                'novo_tipo_garantia',
                'novo_fiador',
                'nova_caucao_meses',
                'nova_caucao_valor',
                'nova_seguro_apolice',
            ),
            'classes': ('collapse',)
        }),
        
        ('Status e Controle', {
            'fields': (
                'status',
                'data_proposta',
                'observacoes',
            ),
        }),
        
        ('Aprovação Proprietário', {
            'fields': (
                'proprietario_aprovou',
                'data_aprovacao_proprietario',
                'ip_aprovacao_proprietario',
                'token_proprietario',
            ),
            'classes': ('collapse',)
        }),
        
        ('Aprovação Locatário', {
            'fields': (
                'locatario_aprovou',
                'data_aprovacao_locatario',
                'ip_aprovacao_locatario',
                'token_locatario',
            ),
            'classes': ('collapse',)
        }),
        
        ('✋ Aprovação Manual (Plano B)', {
            'fields': (
                'aprovacao_manual_proprietario',
                'aprovacao_manual_locatario',
                'motivo_aprovacao_manual',
            ),
            'classes': ('collapse',),
            'description': 'Use para registrar aprovações feitas por telefone/presencial'
        }),
        
        ('📧 Ferramentas de Comunicação', {
            'fields': ('exibir_ferramentas_comunicacao',),
        }),
        
        ('Contrato Gerado', {
            'fields': (
                'nova_locacao',
                'contrato_gerado',
                'data_geracao_contrato',
            ),
            'classes': ('collapse',)
        }),
        
        ('Recusa', {
            'fields': ('motivo_recusa',),
            'classes': ('collapse',)
        }),
    )
    
    # ========================================
    # MÉTODOS DE EXIBIÇÃO
    # ========================================
    
    def numero_contrato_original(self, obj):
        """Exibe número do contrato original"""
        return obj.locacao_original.numero_contrato
    numero_contrato_original.short_description = 'Nº Contrato'
    
    def imovel_info(self, obj):
        """Exibe informações do imóvel"""
        imovel = obj.locacao_original.imovel
        return f"{imovel.endereco}, {imovel.numero}"
    imovel_info.short_description = 'Imóvel'
    
    def locatario_info(self, obj):
        """Exibe nome do locatário"""
        return obj.locacao_original.locatario.nome_razao_social
    locatario_info.short_description = 'Locatário'
    
    def vencimento_info(self, obj):
        """Exibe data de vencimento e dias restantes"""
        dias = obj.dias_para_vencimento
        cor = '#28a745' if dias > settings.ALERTA_MEDIO_DIAS else '#ffc107' if dias > settings.ALERTA_CRITICO_DIAS else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({} dias)</span>',
            cor,
            obj.locacao_original.data_fim.strftime('%d/%m/%Y'),
            dias
        )
    vencimento_info.short_description = 'Vencimento'
    
    def status_badge(self, obj):
        """Badge colorido para status"""
        colors = {
            'rascunho': '#6c757d',
            'pendente_proprietario': '#ff9800',
            'pendente_locatario': '#2196f3',
            'aprovada': '#4caf50',
            'ativa': '#28a745',
            'recusada': '#dc3545',
            'cancelada': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 12px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def acoes_rapidas(self, obj):
        """Botões de ação rápida"""
        url = reverse('admin:core_renovacaocontrato_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">Abrir</a>',
            url
        )
    acoes_rapidas.short_description = 'Ações'
    
    
    def exibir_resumo_proposta(self, obj):
        """Exibe resumo visual da proposta"""
        locacao_atual = obj.locacao_original
        aumento = obj.aumento_percentual
        diferenca = obj.diferenca_aluguel
        
        cor_aumento = '#28a745' if aumento >= 0 else '#dc3545'
        
        html = f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea;">
            <h3 style="margin-top: 0; color: #333;">💰 Comparação de Valores</h3>
            
            <table style="width: 100%; margin-top: 15px;">
                <tr>
                    <td style="padding: 8px; background: white; border-radius: 4px;">
                        <strong>Valor Atual:</strong><br>
                        <span style="font-size: 24px; color: #666;">
                            R$ {locacao_atual.valor_aluguel:,.2f}
                        </span>
                    </td>
                    <td style="text-align: center; padding: 0 20px;">
                        <span style="font-size: 20px;">→</span><br>
                        <span style="background: {cor_aumento}; color: white; padding: 4px 12px; 
                                     border-radius: 12px; font-size: 12px;">
                            {'+' if aumento >= 0 else ''}{aumento:.1f}%
                        </span>
                    </td>
                    <td style="padding: 8px; background: white; border-radius: 4px;">
                        <strong>Valor Novo:</strong><br>
                        <span style="font-size: 24px; color: #28a745;">
                            R$ {obj.novo_valor_aluguel:,.2f}
                        </span>
                    </td>
                </tr>
            </table>
            
            <p style="margin-top: 15px; color: #666;">
                <strong>Diferença mensal:</strong> 
                <span style="color: {cor_aumento};">
                    R$ {diferenca:,.2f}
                </span>
            </p>
            
            <p style="margin: 10px 0 0 0; color: #666; font-size: 13px;">
                <strong>Dias para vencimento:</strong> {obj.dias_para_vencimento} dias
            </p>
        </div>
        """
        return format_html(html)
    exibir_resumo_proposta.short_description = 'Resumo da Proposta'
    
    def exibir_ferramentas_comunicacao(self, obj):
        """
        Exibe ferramentas de comunicação: Email, WhatsApp e Links públicos.
        Esta é a funcionalidade PRINCIPAL dos 3 canais de comunicação.
        """
        locacao_atual = obj.locacao_original
        proprietario = locacao_atual.imovel.locador
        locatario = locacao_atual.locatario
        
        # URLs dos links públicos
        base_url = settings.SITE_URL
        url_proprietario = f"{base_url}/renovacao/proprietario/{obj.token_proprietario}/"
        url_locatario = f"{base_url}/renovacao/locatario/{obj.token_locatario}/"
        
        # Gerar mensagens WhatsApp
        try:
            msg_proprietario = WhatsAppService.gerar_mensagem_renovacao_proprietario(obj)
            tel_proprietario = proprietario.telefone
            link_whatsapp_prop = WhatsAppService.gerar_link_whatsapp(tel_proprietario, msg_proprietario)
        except:
            link_whatsapp_prop = "#"
        
        try:
            msg_locatario = WhatsAppService.gerar_mensagem_renovacao_locatario(obj)
            tel_locatario = locatario.telefone
            link_whatsapp_loc = WhatsAppService.gerar_link_whatsapp(tel_locatario, msg_locatario)
        except:
            link_whatsapp_loc = "#"
        
        html = f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
            
            <!-- PROPRIETÁRIO -->
            <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; 
                        border-left: 4px solid #ff9800;">
                <h3 style="margin-top: 0; color: #ff9800;">📧 Comunicação com Proprietário</h3>
                
                <p><strong>Nome:</strong> {proprietario.nome_razao_social}</p>
                <p><strong>Email:</strong> {proprietario.email or 'Não cadastrado'}</p>
                <p><strong>Telefone:</strong> {proprietario.telefone or 'Não cadastrado'}</p>
                
                <div style="margin-top: 20px;">
                    <h4 style="color: #333;">Canal 1: Email Automático</h4>
                    <button onclick="alert('Funcionalidade de reenvio será implementada via action')" 
                            style="background: #007bff; color: white; border: none; padding: 10px 20px; 
                                   border-radius: 4px; cursor: pointer; margin-right: 10px;">
                        📤 Reenviar Email
                    </button>
                    <small style="color: #666;">
                        Envia email com link de aprovação
                    </small>
                </div>
                
                <div style="margin-top: 20px;">
                    <h4 style="color: #333;">Canal 2: WhatsApp Manual</h4>
                    <a href="{link_whatsapp_prop}" target="_blank"
                       style="display: inline-block; background: #25d366; color: white; 
                              padding: 10px 20px; border-radius: 4px; text-decoration: none; 
                              margin-right: 10px;">
                        💬 Abrir WhatsApp Web
                    </a>
                    <button onclick="navigator.clipboard.writeText('{msg_proprietario}'.replace(/%20/g, ' ').replace(/%0A/g, String.fromCharCode(10))); alert('Mensagem copiada!');" 
                            style="background: #28a745; color: white; border: none; padding: 10px 20px; 
                                   border-radius: 4px; cursor: pointer;">
                        📋 Copiar Mensagem
                    </button>
                </div>
                
                <div style="margin-top: 20px;">
                    <h4 style="color: #333;">Link Público (Compartilhar):</h4>
                    <input type="text" value="{url_proprietario}" readonly 
                           onclick="this.select(); navigator.clipboard.writeText(this.value); alert('Link copiado!');" 
                           style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; 
                                  font-family: monospace; cursor: pointer;">
                    <small style="color: #666;">Clique para copiar</small>
                </div>
                
                <div style="margin-top: 15px; padding: 10px; background: #fff3cd; border-radius: 4px;">
                    <strong>Status:</strong> 
                    {
                        '✅ Aprovado' if obj.proprietario_aprovou == True else 
                        '❌ Rejeitado' if obj.proprietario_aprovou == False else 
                        '⏳ Aguardando resposta'
                    }
                    {f'<br><small>Data: {obj.data_aprovacao_proprietario.strftime("%d/%m/%Y %H:%M")}</small>' 
                     if obj.data_aprovacao_proprietario else ''}
                </div>
            </div>
            
            <!-- LOCATÁRIO (só mostra se proprietário já aprovou) -->
            {'<div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3;">' 
             if obj.status == 'pendente_locatario' or obj.locatario_aprovou is not None else 
             '<div style="background: #e9ecef; padding: 20px; border-radius: 8px; opacity: 0.6;">'}
                <h3 style="margin-top: 0; color: #2196f3;">📧 Comunicação com Locatário</h3>
                
                {'<p style="color: #666; font-style: italic;">Aguardando aprovação do proprietário...</p>' 
                 if obj.status != 'pendente_locatario' and obj.locatario_aprovou is None else f'''
                <p><strong>Nome:</strong> {locatario.nome_razao_social}</p>
                <p><strong>Email:</strong> {locatario.email or 'Não cadastrado'}</p>
                <p><strong>Telefone:</strong> {locatario.telefone or 'Não cadastrado'}</p>
                
                <div style="margin-top: 20px;">
                    <h4 style="color: #333;">Canal 1: Email Automático</h4>
                    <button onclick="alert('Email será enviado automaticamente após aprovação do proprietário')" 
                            style="background: #007bff; color: white; border: none; padding: 10px 20px; 
                                   border-radius: 4px; cursor: pointer;">
                        📤 Reenviar Email
                    </button>
                </div>
                
                <div style="margin-top: 20px;">
                    <h4 style="color: #333;">Canal 2: WhatsApp Manual</h4>
                    <a href="{link_whatsapp_loc}" target="_blank"
                       style="display: inline-block; background: #25d366; color: white; 
                              padding: 10px 20px; border-radius: 4px; text-decoration: none; 
                              margin-right: 10px;">
                        💬 Abrir WhatsApp Web
                    </a>
                    <button onclick="navigator.clipboard.writeText('{msg_locatario}'.replace(/%20/g, ' ').replace(/%0A/g, String.fromCharCode(10))); alert('Mensagem copiada!');" 
                            style="background: #28a745; color: white; border: none; padding: 10px 20px; 
                                   border-radius: 4px; cursor: pointer;">
                        📋 Copiar Mensagem
                    </button>
                </div>
                
                <div style="margin-top: 20px;">
                    <h4 style="color: #333;">Link Público (Compartilhar):</h4>
                    <input type="text" value="{url_locatario}" readonly 
                           onclick="this.select(); navigator.clipboard.writeText(this.value); alert('Link copiado!');" 
                           style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; 
                                  font-family: monospace; cursor: pointer;">
                    <small style="color: #666;">Clique para copiar</small>
                </div>
                
                <div style="margin-top: 15px; padding: 10px; background: #d1ecf1; border-radius: 4px;">
                    <strong>Status:</strong> 
                    {
                        '✅ Aceitou' if obj.locatario_aprovou == True else 
                        '❌ Recusou' if obj.locatario_aprovou == False else 
                        '⏳ Aguardando resposta'
                    }
                    {f'<br><small>Data: {obj.data_aprovacao_locatario.strftime("%d/%m/%Y %H:%M")}</small>' 
                     if obj.data_aprovacao_locatario else ''}
                </div>
                '''}
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; 
                        border-radius: 4px;">
                <strong>💡 Dica:</strong> Use o Canal 3 (Aprovação Manual abaixo) para pessoas sem internet/email.
            </div>
        </div>
        """
        return format_html(html)
    exibir_ferramentas_comunicacao.short_description = 'Ferramentas de Comunicação (3 Canais)'
    
    # ========================================
    # SAVE MODEL (APROVAÇÃO MANUAL)
    # ========================================
    
    def save_model(self, request, obj, form, change):
        """
        Processa aprovações manuais (Plano B).
        Quando admin marca checkbox de aprovação manual, registra como aprovação online.
        """
        
        # Se marcou aprovação manual do proprietário
        if obj.aprovacao_manual_proprietario and obj.proprietario_aprovou is None:
            obj.proprietario_aprovou = True
            obj.data_aprovacao_proprietario = timezone.now()
            obj.ip_aprovacao_proprietario = request.META.get('REMOTE_ADDR', '127.0.0.1')
            obj.status = 'pendente_locatario'
            
            self.message_user(
                request,
                '✅ Aprovação manual do proprietário registrada! '
                'Locatário será notificado.',
                level='success'
            )
            
            # Enviar email ao locatário
            from core.services.email_service import EmailService
            EmailService.notificar_locatario_renovacao(obj)
        
        # Se marcou aprovação manual do locatário
        if obj.aprovacao_manual_locatario and obj.locatario_aprovou is None:
            obj.locatario_aprovou = True
            obj.data_aprovacao_locatario = timezone.now()
            obj.ip_aprovacao_locatario = request.META.get('REMOTE_ADDR', '127.0.0.1')
            obj.status = 'aprovada'
            
            self.message_user(
                request,
                '✅ Aprovação manual do locatário registrada! '
                'Renovação aprovada por ambas as partes.',
                level='success'
            )
        
        super().save_model(request, obj, form, change)
# ════════════════════════════════════════════════════════════════════
# ACTIONS PARA RENOVACAOCONTRATOADMIN
# Adicionar ao final do RenovacaoContratoAdmin em core/admin.py
# ════════════════════════════════════════════════════════════════════

    actions = [
        action_renovar_token_renovacao,
        'enviar_notificacao_renovacao_email',
        'enviar_notificacao_renovacao_whatsapp',
        'gerar_contrato_renovacao', 'gerar_contrato_pdf_renovacao', 'enviar_contrato_email', 'enviar_contrato_whatsapp', 'ativar_renovacao']
    
    @admin.action(description='📝 Gerar Contrato de Renovação (DOCX)')
    def gerar_contrato_renovacao(self, request, queryset):
        """
        Gera contrato DOCX para renovação.
        Usa sistema de templates + variáveis de renovação.
        """
        if queryset.count() != 1:
            self.message_user(
                request,
                '❌ Selecione apenas UMA renovação por vez',
                level='error'
            )
            return
        
        renovacao = queryset.first()
        
        if renovacao.status != 'aprovada':
            self.message_user(
                request,
                f'❌ Renovação deve estar APROVADA (status atual: {renovacao.get_status_display()})',
                level='error'
            )
            return
        
        # Criar nova locação se não existe
        if not renovacao.nova_locacao:
            try:
                nova_locacao = Locacao.objects.create(
                    imovel=renovacao.locacao_original.imovel,
                    locatario=renovacao.locacao_original.locatario,
                    data_inicio=renovacao.nova_data_inicio,
                    data_fim=renovacao.nova_data_fim,
                    valor_aluguel=renovacao.novo_valor_aluguel,
                    dia_vencimento=renovacao.locacao_original.dia_vencimento,
                    tipo_garantia=renovacao.novo_tipo_garantia,
                    fiador_garantia=renovacao.novo_fiador,
                    caucao_quantidade_meses=renovacao.nova_caucao_meses,
                    seguro_apolice=renovacao.nova_seguro_apolice,
                    status='PENDING',
                )
                
                renovacao.nova_locacao = nova_locacao
                renovacao.data_geracao_contrato = timezone.now()
                renovacao.save()
                
            except Exception as e:
                self.message_user(
                    request,
                    f'❌ Erro ao criar nova locação: {e}',
                    level='error'
                )
                return
        
        # Gerar contrato de renovação
        from core.views_gerar_contrato import gerar_docx_contrato_renovacao
        from django.http import HttpResponse
        
        try:
            # Gerar DOCX
            docx_io = gerar_docx_contrato_renovacao(renovacao)
            
            # Preparar resposta
            filename = f'Contrato_Renovacao_{renovacao.locacao_original.numero_contrato}.docx'
            
            response = HttpResponse(
                docx_io.read(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            self.message_user(
                request,
                f'✅ Contrato de renovação gerado: {filename}',
                level='success'
            )
            
            return response
            
        except Exception as e:
            import traceback
            self.message_user(
                request,
                f'❌ Erro ao gerar contrato: {e}',
                level='error'
            )
    
    
    @admin.action(description='📄 Gerar Contrato de Renovação (PDF)')
    def gerar_contrato_pdf_renovacao(self, request, queryset):
        """
        Gera contrato PDF para renovação.
        Usa DOCX → PDF via LibreOffice.
        """
        if queryset.count() != 1:
            self.message_user(
                request,
                '❌ Selecione apenas UMA renovação por vez',
                level='error'
            )
            return
        
        renovacao = queryset.first()
        
        if renovacao.status != 'aprovada':
            self.message_user(
                request,
                f'❌ Renovação deve estar APROVADA (status atual: {renovacao.get_status_display()})',
                level='error'
            )
            return
        
        # Criar nova locação se não existe
        if not renovacao.nova_locacao:
            try:
                nova_locacao = Locacao.objects.create(
                    imovel=renovacao.locacao_original.imovel,
                    locatario=renovacao.locacao_original.locatario,
                    data_inicio=renovacao.nova_data_inicio,
                    data_fim=renovacao.nova_data_fim,
                    valor_aluguel=renovacao.novo_valor_aluguel,
                    dia_vencimento=renovacao.locacao_original.dia_vencimento,
                    tipo_garantia=renovacao.novo_tipo_garantia,
                    fiador_garantia=renovacao.novo_fiador,
                    caucao_quantidade_meses=renovacao.nova_caucao_meses,
                    seguro_apolice=renovacao.nova_seguro_apolice,
                    status='PENDING',
                )
                
                renovacao.nova_locacao = nova_locacao
                renovacao.data_geracao_contrato = timezone.now()
                renovacao.save()
                
            except Exception as e:
                self.message_user(
                    request,
                    f'❌ Erro ao criar nova locação: {e}',
                    level='error'
                )
                return
        
        # Gerar DOCX primeiro, depois converter para PDF
        from core.views_gerar_contrato import gerar_docx_contrato_renovacao, converter_docx_para_pdf
        from django.http import HttpResponse
        
        try:
            # 1. Gerar DOCX
            docx_io = gerar_docx_contrato_renovacao(renovacao)
            
            # 2. Converter para PDF
            pdf_io = converter_docx_para_pdf(docx_io)
            
            if not pdf_io:
                raise Exception('Falha ao gerar PDF. Verifique se LibreOffice está instalado.')
            
            # 3. Preparar resposta
            filename = f'Contrato_Renovacao_{renovacao.locacao_original.numero_contrato}.pdf'
            
            response = HttpResponse(
                pdf_io.read(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            self.message_user(
                request,
                f'✅ Contrato PDF gerado: {filename}',
                level='success'
            )
            
            return response
            
        except Exception as e:
            import traceback
            self.message_user(
                request,
                f'❌ Erro ao gerar PDF: {e}',
                level='error'
            )

    @admin.action(description='📧 Enviar Contrato por Email')
    def enviar_contrato_email(self, request, queryset):
        """
        Envia contrato por email para proprietário e locatário.
        """
        if queryset.count() != 1:
            self.message_user(
                request,
                '❌ Selecione apenas UMA renovação por vez',
                level='error'
            )
            return
        
        renovacao = queryset.first()
        
        if not renovacao.nova_locacao:
            self.message_user(
                request,
                '❌ Contrato ainda não foi gerado. Execute "Gerar Contrato" primeiro.',
                level='error'
            )
            return
        
        from django.core.mail import EmailMessage
        from core.views_gerar_contrato import gerar_contrato_docx
        import io
        
        try:
            # Gerar DOCX de RENOVAÇÃO (com variáveis específicas)
            from core.views_gerar_contrato import gerar_docx_contrato_renovacao, converter_docx_para_pdf
            
            docx_io = gerar_docx_contrato_renovacao(renovacao)
            
            # Converter para PDF
            pdf_io = converter_docx_para_pdf(docx_io)
            
            if not pdf_io:
                raise Exception('Falha ao converter contrato para PDF')
            
            pdf_content = pdf_io.read()
            
            locacao = renovacao.locacao_original
            proprietario = locacao.imovel.locador
            locatario = locacao.locatario
            
            # Criar email
            email = EmailMessage(
                subject=f'Contrato de Renovação - {locacao.imovel.endereco_completo}',
                body=f"""
Prezados,

Segue em anexo o contrato de renovação já aprovado por ambas as partes.

Dados da Renovação:
- Imóvel: {locacao.imovel.endereco_completo}
- Locatário: {locatario.nome_razao_social}
- Vigência: {renovacao.nova_data_inicio.strftime('%d/%m/%Y')} a {renovacao.nova_data_fim.strftime('%d/%m/%Y')}
- Valor Anterior: R$ {renovacao.locacao_original.valor_aluguel:,.2f}
- Valor Novo: R$ {renovacao.novo_valor_aluguel:,.2f}
- Reajuste: {renovacao.aumento_percentual:.1f}%

Por favor, imprimam, assinem e devolvam 2 vias.

Atenciosamente,
HABITAT PRO - A&C Imóveis e Sistemas Imobiliários

                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[proprietario.email, locatario.email],
            )
            
            # Anexar PDF (não DOCX)
            email.attach(
                f'Contrato_Renovacao_{renovacao.nova_locacao.numero_contrato}.pdf',
                pdf_content,
                'application/pdf'
            )
            
            email.send()
            
            self.message_user(
                request,
                f'✅ Email enviado com sucesso para:\n'
                f'   • {proprietario.email}\n'
                f'   • {locatario.email}',
                level='success'
            )
            
        except Exception as e:
            self.message_user(
                request,
                f'❌ Erro ao enviar email: {e}',
                level='error'
            )
    
    @admin.action(description='💬 Enviar Contrato por WhatsApp')
    def enviar_contrato_whatsapp(self, request, queryset):
        """Gera link wa.me para enviar contrato via WhatsApp com link de download seguro"""
        if queryset.count() != 1:
            self.message_user(request, '❌ Selecione apenas UMA renovação por vez', level='error')
            return
        
        renovacao = queryset.first()
        
        if not renovacao.nova_locacao:
            self.message_user(request, '❌ Contrato ainda não foi gerado. Execute "Gerar Contrato" primeiro.', level='error')
            return
        
        from urllib.parse import quote
        from django.urls import reverse
        from core.models import ContratoDownloadToken
        
        locacao = renovacao.locacao_original
        locatario = locacao.locatario
        imovel = locacao.imovel
        
        # Criar token de download
        try:
            token = ContratoDownloadToken.criar_token(renovacao=renovacao, tipo_destinatario='locatario', dias_validade=7)
            download_url = request.build_absolute_uri(reverse('download_contrato_token', kwargs={'token': token.token}))
        except Exception as e:
            self.message_user(request, f'❌ Erro ao criar link de download: {e}', level='error')
            return
        
        # Preparar telefone
        telefone = ''.join(filter(str.isdigit, locatario.telefone))
        if not telefone.startswith('55'):
            telefone = f'55{telefone}'
        
        # Mensagem padronizada
        mensagem = f"""🏠 *HABITAT PRO - Contrato de Renovação*

Olá *{locatario.nome_razao_social}*,

Seu contrato de renovação foi aprovado! ✅

📋 *Dados da Renovação:*
- Imóvel: {imovel.endereco_completo}
- Vigência: {renovacao.nova_data_inicio.strftime('%d/%m/%Y')} a {renovacao.nova_data_fim.strftime('%d/%m/%Y')}
- Valor Anterior: R$ {renovacao.locacao_original.valor_aluguel:,.2f}
- Valor Novo: R$ {renovacao.novo_valor_aluguel:,.2f}
- Reajuste: {renovacao.aumento_percentual:.1f}%

📄 *BAIXAR CONTRATO (PDF):*
{download_url}

⏰ Link válido por 7 dias

Por favor, imprima, assine e devolva 2 vias.

*HABITAT PRO - A&C Imóveis e Sistemas Imobiliários*"""
        
        mensagem_encoded = quote(mensagem)
        whatsapp_url = f'https://wa.me/{telefone}?text={mensagem_encoded}'
        request.session['whatsapp_redirect'] = whatsapp_url
        
        self.message_user(request, format_html(
            '✅ Link WhatsApp gerado com link de download seguro!<br>'
            '📄 Token válido por 7 dias<br>'
            '🔗 Total de acessos será registrado<br><br>'
            '<a href="{}" target="_blank" style="background:#25d366;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;display:inline-block;margin-top:10px;">💬 Abrir WhatsApp Web</a>',
            whatsapp_url), level='success')
    
    @admin.action(description='✅ Ativar Renovação (Criar Novo Contrato)')
    def ativar_renovacao(self, request, queryset):
        """
        Ativa a renovação:
        1. Inativa contrato antigo
        2. Ativa contrato novo
        3. Sistema gera comandas automaticamente
        """
        if queryset.count() != 1:
            self.message_user(
                request,
                '❌ Selecione apenas UMA renovação por vez',
                level='error'
            )
            return
        
        renovacao = queryset.first()
        
        # Validações
        if renovacao.status != 'aprovada':
            self.message_user(
                request,
                f'❌ Renovação deve estar APROVADA (status atual: {renovacao.get_status_display()})',
                level='error'
            )
            return
        
        if not renovacao.nova_locacao:
            self.message_user(
                request,
                '❌ Contrato ainda não foi gerado. Execute "Gerar Contrato" primeiro.',
                level='error'
            )
            return
        
        # Ativar renovação
        try:
            # Inativar contrato antigo
            renovacao.locacao_original.status = 'INACTIVE'
            renovacao.locacao_original.save()
            
            # Ativar contrato novo
            renovacao.nova_locacao.status = 'ACTIVE'
            renovacao.nova_locacao.save()
            
            # Atualizar status da renovação
            renovacao.status = 'ativa'
            renovacao.save()
            
            self.message_user(
                request,
                format_html(
                    '✅ <strong>Renovação ativada com sucesso!</strong><br><br>'
                    '📋 Contrato Antigo: {} → <span style="color: #dc3545;">INATIVO</span><br>'
                    '📋 Contrato Novo: {} → <span style="color: #28a745;">ATIVO</span><br><br>'
                    '💡 Comandas serão geradas automaticamente a partir de {}',
                    renovacao.locacao_original.numero_contrato,
                    renovacao.nova_locacao.numero_contrato,
                    renovacao.nova_data_inicio.strftime('%d/%m/%Y')
                ),
                level='success'
            )
            
        except Exception as e:
            self.message_user(
                request,
                f'❌ Erro ao ativar renovação: {e}',
                level='error'
            )

    # ════════════════════════════════════════════════════════════════
    # ACTION: ENVIAR NOTIFICAÇÃO DE RENOVAÇÃO
    # ════════════════════════════════════════════════════════════════
    
    @admin.action(description='🔔 Enviar Notificação de Renovação (Email)')
    def enviar_notificacao_renovacao_email(self, request, queryset):
        """
        Envia notificação por email para proprietário e locatário
        com links públicos para aprovação/rejeição da renovação.
        
        O email contém:
        - Detalhes da proposta de renovação
        - Link público para PROPRIETÁRIO responder (aprovar/rejeitar)
        - Link público para LOCATÁRIO responder (aprovar/rejeitar)
        - Sem necessidade de login no sistema
        """
        from core.services.email_service import EmailService
        
        enviados_prop = 0
        enviados_loc = 0
        erros = 0
        detalhes_erros = []
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 ACTION DEBUG 1: Iniciando enviar_notificacao_renovacao_email com {queryset.count()} renovações")
        
        for renovacao in queryset:
            logger.info(f"🔍 ACTION DEBUG 2: Processando renovacao id={renovacao.id}")
            logger.info(f"🔍 ACTION DEBUG 3: renovacao.__dict__ = {renovacao.__dict__}")
            try:
                # Validar se renovação NÃO está finalizada
                # Bloqueia apenas: ativa, recusada, cancelada
                # Permite: rascunho, pendente_proprietario, pendente_locatario, aprovada
                if renovacao.status in ['ativa', 'recusada', 'cancelada']:
                    detalhes_erros.append(
                        f"Renovação {renovacao.locacao_original.numero_contrato}: "
                        f"Status '{renovacao.get_status_display()}' não permite envio (processo finalizado)"
                    )
                    erros += 1
                    continue
                
                # Enviar para proprietário
                try:
                    EmailService.notificar_proprietario_renovacao(renovacao)
                    enviados_prop += 1
                except Exception as e:
                    detalhes_erros.append(
                        f"Erro ao enviar para proprietário de {renovacao.locacao_original.numero_contrato}: {str(e)}"
                    )
                    erros += 1
                
                # Enviar para locatário
                try:
                    EmailService.notificar_locatario_renovacao(renovacao)
                    enviados_loc += 1
                except Exception as e:
                    detalhes_erros.append(
                        f"Erro ao enviar para locatário de {renovacao.locacao_original.numero_contrato}: {str(e)}"
                    )
                    erros += 1
                
            except Exception as e:
                erros += 1
                detalhes_erros.append(
                    f"Erro geral em {renovacao.locacao_original.numero_contrato}: {str(e)}"
                )
        
        # Mensagens de feedback
        total_emails = enviados_prop + enviados_loc
        
        if total_emails > 0:
            self.message_user(
                request,
                f"✅ {total_emails} email(s) enviado(s) com sucesso! "
                f"(Proprietários: {enviados_prop}, Locatários: {enviados_loc})",
                level='SUCCESS'
            )
        
        if erros > 0:
            self.message_user(
                request,
                f"⚠️ {erros} erro(s) ao enviar notificações",
                level='WARNING'
            )
            
            # Mostrar detalhes dos erros
            for detalhe in detalhes_erros[:5]:  # Máximo 5 erros detalhados
                self.message_user(request, f"  • {detalhe}", level='ERROR')
    

    @admin.action(description='💬 Enviar Notificação de Renovação (WhatsApp)')
    def enviar_notificacao_renovacao_whatsapp(self, request, queryset):
        """Gera links wa.me para notificação via WhatsApp"""
        from core.services.whatsapp_service import WhatsAppService
        from django.utils.safestring import mark_safe
        
        links_gerados = []
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 ACTION DEBUG 1: Iniciando enviar_notificacao_renovacao_email com {queryset.count()} renovações")
        
        for renovacao in queryset:
            logger.info(f"🔍 ACTION DEBUG 2: Processando renovacao id={renovacao.id}")
            logger.info(f"🔍 ACTION DEBUG 3: renovacao.__dict__ = {renovacao.__dict__}")
            # Bloqueia apenas renovações finalizadas
            if renovacao.status in ['ativa', 'recusada', 'cancelada']:
                continue
            
            locacao_atual = renovacao.locacao_original
            
            # Proprietário
            try:
                proprietario = locacao_atual.imovel.locador
                if proprietario.telefone:
                    msg = WhatsAppService.gerar_mensagem_renovacao_proprietario(renovacao)
                    link = WhatsAppService.gerar_link_whatsapp(proprietario.telefone, msg)
                    links_gerados.append({
                        'tipo': 'Proprietário',
                        'nome': proprietario.nome_razao_social,
                        'contrato': renovacao.locacao_original.numero_contrato,
                        'link': link
                    })
            except:
                pass
            
            # Locatário
            try:
                locatario = locacao_atual.locatario
                if locatario.telefone:
                    msg = WhatsAppService.gerar_mensagem_renovacao_locatario(renovacao)
                    link = WhatsAppService.gerar_link_whatsapp(locatario.telefone, msg)
                    links_gerados.append({
                        'tipo': 'Locatário',
                        'nome': locatario.nome_razao_social,
                        'contrato': renovacao.locacao_original.numero_contrato,
                        'link': link
                    })
            except:
                pass
        
        if links_gerados:
            html = f"<div><h3>💬 {len(links_gerados)} Link(s) WhatsApp</h3>"
            for info in links_gerados:
                html += f"""
                <div style='margin:10px 0; padding:10px; background:#f0f0f0;'>
                    <p><b>{info['tipo']}:</b> {info['nome']}<br>
                    <b>Contrato:</b> {info['contrato']}</p>
                    <a href='{info['link']}' target='_blank' 
                       style='background:#25D366; color:white; padding:8px 15px; 
                              text-decoration:none; border-radius:4px; display:inline-block;'>
                        Abrir WhatsApp ➜
                    </a>
                </div>
                """
            html += "</div>"
            self.message_user(request, mark_safe(html), level='SUCCESS')
        else:
            self.message_user(request, "Nenhum link gerado", level='WARNING')



# ═══════════════════════════════════════════════════════════════
# CUSTOM ADMIN SITE COM WIDGETS DE TOKENS (DEV_21.6 - Fase 4)
# ═══════════════════════════════════════════════════════════════

from django.contrib.admin import AdminSite
from django.shortcuts import render

class CustomAdminSite(AdminSite):
    """Admin site customizado com widgets de monitoramento de tokens."""
    
    def index(self, request, extra_context=None):
        """
        Override do index para adicionar contexto dos tokens.
        """
        extra_context = extra_context or {}
        
        # Adicionar contexto dos tokens
        try:
            contexto_tokens = gerar_contexto_dashboard()
            extra_context.update(contexto_tokens)
        except Exception as e:
            # Se der erro, não quebrar o admin
            print(f"Erro ao carregar widgets de tokens: {e}")
        
        return super().index(request, extra_context=extra_context)

# Usar custom admin site
# admin_site = CustomAdminSite(name='admin')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADMIN DE VISTORIAS (Inspection System)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from core.admin_inspection import (
    InspectionAdmin,
    InspectionPhotoAdmin,
    InspectionPDFAdmin
)
# Os modelos já estão registrados com @admin.register no admin_inspection.py

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADMIN DE RESCISÃO (Módulo Isolado)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from core.admin_rescisao import RescisaoContratoAdmin, ComandaRescisaoAdmin
