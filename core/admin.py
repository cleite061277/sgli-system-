
from django.contrib import admin
from django import forms
from core.models import ConfiguracaoSistema, LogGeracaoComandas
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .forms import PagamentoAdminForm
from .models import Fiador, Usuario, Locador, Imovel, Locatario, Locacao, Comanda, Pagamento, TemplateContrato
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
        """Exibe alerta para contratos vencendo em até 60 dias"""
        from django.utils import timezone
        from django.utils.html import format_html
        
        if not obj.data_fim:
            return '-'
        
        hoje = timezone.now().date()
        dias_restantes = (obj.data_fim - hoje).days
        
        if 0 <= dias_restantes <= 60:
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

    def get_form(self, request, obj=None, **kwargs):
        """Remove required do numero_contrato para permitir geração automática"""
        form = super().get_form(request, obj, **kwargs)
        if 'numero_contrato' in form.base_fields:
            form.base_fields['numero_contrato'].required = False
        return form

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
        
        comanda_url = f"{domain}/comanda/{obj.id}/web/"
        
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
{imovel.endereco}, {imovel.numero}

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
            '<a href="/comanda/{}/web/" target="_blank" style="background:#8b5cf6;color:white;padding:6px 12px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:11px;">👁️ Ver</a>',
            wa_url, obj.id, obj.id
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
   # list_display = ('numero_comanda', 'locacao', 'mes_referencia', 'ano_referencia', 'status', 'data_vencimento')
   # list_filter = ('status', 'ano_referencia', 'mes_referencia', 'is_active')
   # search_fields = ('numero_comanda', 'locacao__numero_contrato', 'locacao__locatario__nome_razao_social')
   # readonly_fields = ('numero_comanda',)

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    form = PagamentoAdminForm
    
    actions = ['gerar_recibo']
    
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
    list_display = ('numero_pagamento', 'comanda', 'locatario_nome', 'valor_pago', 'data_pagamento', 'forma_pagamento', 'status', 'botao_recibo')
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
    
    def locatario_nome(self, obj):
        """Display tenant name in list."""
        return obj.comanda.locacao.locatario.nome_razao_social
    locatario_nome.short_description = 'Locatário'
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
        """Display clickable contract information."""
        from django.utils.html import format_html
        from django.urls import reverse
        
        locacao = obj.comanda.locacao
        locatario = locacao.locatario
        imovel = locacao.imovel
        
        # URL para locação
        url_locacao = reverse('admin:core_locacao_change', args=[locacao.id])
        # URL para locatário
        url_locatario = reverse('admin:core_locatario_change', args=[locatario.id])
        
        return format_html(
            '<div style="padding: 10px; background: #f8f9fa; border-radius: 5px;">'
            '<strong>Contrato:</strong> <a href="{}" target="_blank" style="color: #007bff;">{}</a><br>'
            '<strong>Locatário:</strong> <a href="{}" target="_blank" style="color: #007bff;">{}</a><br>'
            '<strong>Imóvel:</strong> {}<br>'
            '<strong>Valor Aluguel:</strong> R$ {:.2f}'
            '</div>',
            url_locacao,
            locacao.numero_contrato,
            url_locatario,
            locatario.nome_razao_social,
            imovel.endereco_completo,
            locacao.valor_aluguel
        )
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
