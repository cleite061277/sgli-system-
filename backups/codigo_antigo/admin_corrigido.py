"""
Django Admin - Habitat Pro
CORRIGIDO: Botões adicionados nas classes corretas
"""
from django.contrib import admin
from django.utils.html import format_html, escape
from django.urls import reverse, path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from .models import (
    Usuario, Locador, Imovel, Locatario, Fiador, Locacao, 
    Comanda, Pagamento, TemplateContrato, ConfiguracaoSistema,
    LogGeracaoComandas
)


# ════════════════════════════════════════════════════════════
# USUARIO ADMIN
# ════════════════════════════════════════════════════════════

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'is_active', 'is_staff']
    list_filter = ['tipo_usuario', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('username', 'email', 'first_name', 'last_name')
        }),
        ('Tipo e Permissões', {
            'fields': ('tipo_usuario', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Datas', {
            'fields': ('date_joined', 'last_login')
        }),
    )
    readonly_fields = ['date_joined', 'last_login']


# ════════════════════════════════════════════════════════════
# LOCADOR ADMIN
# ════════════════════════════════════════════════════════════

@admin.register(Locador)
class LocadorAdmin(admin.ModelAdmin):
    list_display = ['nome_razao_social', 'cpf_cnpj', 'tipo_pessoa', 'email', 'telefone']
    list_filter = ['tipo_pessoa', 'created_at']
    search_fields = ['nome_razao_social', 'cpf_cnpj', 'email', 'telefone']
    fieldsets = (
        ('Identificação', {
            'fields': ('nome_razao_social', 'tipo_pessoa', 'cpf_cnpj', 'rg_ie')
        }),
        ('Contato', {
            'fields': ('email', 'telefone', 'celular')
        }),
        ('Endereço', {
            'fields': ('endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep')
        }),
        ('Dados Bancários', {
            'fields': ('banco', 'agencia', 'conta', 'tipo_conta', 'pix')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )


# ════════════════════════════════════════════════════════════
# IMOVEL ADMIN
# ════════════════════════════════════════════════════════════

@admin.register(Imovel)
class ImovelAdmin(admin.ModelAdmin):
    list_display = ['codigo_imovel', 'endereco', 'numero', 'tipo_imovel', 'locador', 'status', 'valor_aluguel']
    list_filter = ['status', 'tipo_imovel', 'created_at']
    search_fields = ['codigo_imovel', 'endereco', 'locador__nome_razao_social']
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo_imovel', 'locador', 'status')
        }),
        ('Endereço', {
            'fields': ('endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep')
        }),
        ('Características', {
            'fields': ('tipo_imovel', 'area_construida', 'area_total', 'quartos', 'banheiros', 'vagas_garagem')
        }),
        ('Valores', {
            'fields': ('valor_aluguel', 'valor_condominio', 'valor_iptu')
        }),
        ('Descrição', {
            'fields': ('descricao',),
            'classes': ('collapse',)
        }),
    )


# ════════════════════════════════════════════════════════════
# LOCATARIO ADMIN
# ════════════════════════════════════════════════════════════

@admin.register(Locatario)
class LocatarioAdmin(admin.ModelAdmin):
    list_display = ['nome_razao_social', 'cpf_cnpj', 'tipo_pessoa', 'email', 'telefone']
    list_filter = ['tipo_pessoa', 'estado_civil', 'created_at']
    search_fields = ['nome_razao_social', 'cpf_cnpj', 'email', 'telefone']
    fieldsets = (
        ('Identificação', {
            'fields': ('nome_razao_social', 'tipo_pessoa', 'cpf_cnpj', 'rg_ie', 'data_nascimento', 'nacionalidade', 'estado_civil')
        }),
        ('Contato', {
            'fields': ('email', 'telefone', 'celular')
        }),
        ('Endereço', {
            'fields': ('endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep')
        }),
        ('Profissão', {
            'fields': ('profissao', 'empresa', 'renda_mensal')
        }),
        ('Referências', {
            'fields': ('referencia_nome', 'referencia_telefone'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )


# ════════════════════════════════════════════════════════════
# FIADOR ADMIN
# ════════════════════════════════════════════════════════════

@admin.register(Fiador)
class FiadorAdmin(admin.ModelAdmin):
    list_display = ['nome_completo', 'cpf', 'email', 'telefone', 'estado_civil']
    list_filter = ['estado_civil', 'created_at']
    search_fields = ['nome_completo', 'cpf', 'email', 'telefone']
    fieldsets = (
        ('Identificação', {
            'fields': ('nome_completo', 'cpf', 'rg', 'data_nascimento', 'nacionalidade', 'estado_civil')
        }),
        ('Contato', {
            'fields': ('email', 'telefone', 'celular')
        }),
        ('Endereço', {
            'fields': ('endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep')
        }),
        ('Profissão', {
            'fields': ('profissao', 'empresa', 'renda_mensal')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )


# ════════════════════════════════════════════════════════════
# LOCACAO ADMIN
# ════════════════════════════════════════════════════════════

@admin.register(Locacao)
class LocacaoAdmin(admin.ModelAdmin):
    list_display = ['numero_contrato', 'imovel', 'locatario', 'data_inicio', 'data_fim', 'status', 'valor_aluguel']
    list_filter = ['status', 'tipo_contrato', 'data_inicio', 'data_fim']
    search_fields = ['numero_contrato', 'imovel__endereco', 'locatario__nome_razao_social']
    date_hierarchy = 'data_inicio'
    
    fieldsets = (
        ('Contrato', {
            'fields': ('numero_contrato', 'imovel', 'locatario', 'fiador', 'status')
        }),
        ('Período', {
            'fields': ('data_inicio', 'data_fim', 'tipo_contrato', 'prazo_meses')
        }),
        ('Valores', {
            'fields': ('valor_aluguel', 'dia_vencimento', 'indice_reajuste', 'percentual_multa', 'percentual_juros')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = []


# ════════════════════════════════════════════════════════════
# COMANDA ADMIN
# ════════════════════════════════════════════════════════════

@admin.register(Comanda)
class ComandaAdmin(admin.ModelAdmin):
    list_display = [
        'numero_comanda',
        'locacao',
        'mes_referencia',
        'ano_referencia',
        'status_badge',
        'data_vencimento',
        'valor_total',
        'painel_whatsapp_button',
    ]
    
    list_filter = ['status', 'mes_referencia', 'ano_referencia', 'data_vencimento']
    search_fields = ['numero_comanda', 'locacao__numero_contrato', 'locacao__locatario__nome_razao_social']
    date_hierarchy = 'data_vencimento'
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_comanda', 'locacao', 'mes_referencia', 'ano_referencia', 'status')
        }),
        ('Vencimento', {
            'fields': ('data_vencimento', 'data_pagamento')
        }),
        ('Valores', {
            'fields': (
                'valor_aluguel',
                'valor_condominio',
                'valor_iptu',
                'valor_administracao',
                'outros_debitos',
                'outros_creditos',
                'desconto',
                'valor_multa',
                'valor_juros',
            )
        }),
        ('Pagamento', {
            'fields': ('valor_pago', 'forma_pagamento')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = []
    
    def status_badge(self, obj):
        """Badge colorido para o status"""
        colors = {
            'PENDING': '#FFA500',
            'PAGA': '#28A745',
            'ATRASADA': '#DC3545',
            'PARCIAL': '#17A2B8',
            'CANCELADA': '#6C757D',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#6C757D'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def painel_whatsapp_button(self, obj):
        """Botão para abrir painel WhatsApp"""
        return format_html(
            '<a class="button" href="/admin/whatsapp/" '
            'style="background-color: #25D366; color: white; padding: 5px 10px; '
            'border-radius: 5px; text-decoration: none;">'
            '💬 Painel WhatsApp</a>'
        )
    painel_whatsapp_button.short_description = 'WhatsApp'


# ════════════════════════════════════════════════════════════
# PAGAMENTO ADMIN
# ════════════════════════════════════════════════════════════

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_pagamento',
        'comanda_link',
        'data_pagamento',
        'valor_pago',
        'forma_pagamento',
        'locatario_link',
        'recibo_button',
    ]
    
    list_filter = ['forma_pagamento', 'data_pagamento', 'created_at']
    search_fields = ['numero_pagamento', 'comanda__numero_comanda', 'comanda__locacao__locatario__nome_razao_social']
    date_hierarchy = 'data_pagamento'
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_pagamento', 'comanda', 'usuario_registro')
        }),
        ('Pagamento', {
            'fields': ('data_pagamento', 'valor_pago', 'forma_pagamento')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['usuario_registro']
    
    def comanda_link(self, obj):
        """Link clicável para a comanda"""
        if obj.comanda:
            url = reverse('admin:core_comanda_change', args=[obj.comanda.id])
            return format_html('<a href="{}">{}</a>', url, obj.comanda.numero_comanda)
        return '-'
    comanda_link.short_description = 'Comanda'
    comanda_link.admin_order_field = 'comanda__numero_comanda'
    
    def locatario_link(self, obj):
        """Link clicável para o locatário"""
        if obj.comanda and obj.comanda.locacao and obj.comanda.locacao.locatario:
            locatario = obj.comanda.locacao.locatario
            url = reverse('admin:core_locatario_change', args=[locatario.id])
            return format_html('<a href="{}">{}</a>', url, locatario.nome_razao_social)
        return '-'
    locatario_link.short_description = 'Locatário'
    
    def recibo_button(self, obj):
        """Botão para acessar página de recibo"""
        url = reverse('pagina_recibo_pagamento', args=[obj.id])
        return format_html(
            '<a class="button" href="{}" '
            'style="background-color: #667eea; color: white; padding: 5px 10px; '
            'border-radius: 5px; text-decoration: none;" target="_blank">'
            '🧾 Recibo</a>',
            url
        )
    recibo_button.short_description = 'Recibo'


# ════════════════════════════════════════════════════════════
# OUTROS ADMINS
# ════════════════════════════════════════════════════════════

@admin.register(TemplateContrato)
class TemplateContratoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo', 'created_at']
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome']


@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):
    list_display = ['chave', 'valor', 'updated_at']
    search_fields = ['chave', 'valor']


@admin.register(LogGeracaoComandas)
class LogGeracaoComandasAdmin(admin.ModelAdmin):
    list_display = ['mes_referencia', 'ano_referencia', 'quantidade_gerada', 'usuario', 'created_at']
    list_filter = ['mes_referencia', 'ano_referencia', 'created_at']
    readonly_fields = ['mes_referencia', 'ano_referencia', 'quantidade_gerada', 'usuario', 'created_at']


# ════════════════════════════════════════════════════════════
# CUSTOMIZAÇÕES DO ADMIN SITE
# ════════════════════════════════════════════════════════════

admin.site.site_header = "HABITAT PRO - Gestão Imobiliária"
admin.site.site_title = "HABITAT PRO Admin"
admin.site.index_title = "Painel Administrativo"
