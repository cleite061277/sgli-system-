"""
Admin para Sistema de Vistorias
Autor: Claude + Cícero (Policorp)
Data: 11/01/2026
"""
from django.contrib import admin
from django.shortcuts import render
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from django.conf import settings
from core.models_inspection import Inspection, InspectionPhoto, InspectionPDF
from core.services.inspection_pdf import gerar_pdf_vistoria


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INLINE ADMIN - FOTOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class InspectionPhotoInline(admin.TabularInline):
    """Inline para fotos da vistoria"""
    model = InspectionPhoto
    extra = 0
    fields = ('ordem', 'legenda', 'tamanho_mb', 'largura', 'altura', 'tirada_em')
    readonly_fields = ('tamanho_mb', 'largura', 'altura', 'tirada_em')
    can_delete = True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INSPECTION ADMIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    """Admin para Vistorias"""
    
    list_display = (
        'titulo',
        'numero_contrato',
        'renovacao_badge',
        'imovel_endereco',
        'status_badge',
        'total_fotos',
        'pdf_badge',
        'link_publico',
        'created_at'
    )
    
    list_filter = ('status', 'created_at')
    
    search_fields = (
        'titulo',
        'locacao__numero_contrato',
        'locacao__imovel__endereco',
        'inspector_nome'
    )
    
    readonly_fields = (
        'token',
        'token_expires_at',
        'scheduled_at',
        'started_at',
        'completed_at',
        'created_at',
        'updated_at',
        'link_publico_display',
        'pdf_download_link'
    )
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'locacao',
                'renovacao',
                'titulo',
                'descricao',
                'status'
            )
        }),
        ('Inspector', {
            'fields': (
                'inspector_nome',
                'inspector_contato'
            )
        }),
        ('Token de Acesso', {
            'fields': (
                'token',
                'token_expires_at',
                'link_publico_display'
            )
        }),
        ('Timestamps', {
            'fields': (
                'scheduled_at',
                'started_at',
                'completed_at',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
        ('PDF Gerado', {
            'fields': ('pdf_download_link',)
        })
    )
    
    inlines = [InspectionPhotoInline]
    
    actions = [
        'gerar_pdf_action',
        'renovar_token_action',
        'enviar_por_email_action',
        'enviar_por_whatsapp_action'
    ]
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # LIST DISPLAY METHODS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def numero_contrato(self, obj):
        return obj.locacao.numero_contrato
    numero_contrato.short_description = 'Contrato'
    
    def imovel_endereco(self, obj):
        imovel = obj.locacao.imovel
        return f"{imovel.endereco}, {imovel.numero}"
    imovel_endereco.short_description = 'Imóvel'
    
    def renovacao_badge(self, obj):
        if obj.renovacao:
            return format_html(
                '<span style="background: #fbbf24; color: #78350f; padding: 4px 12px; '
                'border-radius: 12px; font-size: 11px; font-weight: 600;">🔄 Renovação</span>'
            )
        return format_html('<span style="color: #d1d5db;">-</span>')
    renovacao_badge.short_description = 'Renovação'
    
    def status_badge(self, obj):
        colors = {
            'scheduled': '#fbbf24',
            'in_progress': '#3b82f6',
            'completed': '#10b981',
            'cancelled': '#ef4444'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            colors.get(obj.status, '#6b7280'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def pdf_badge(self, obj):
        if obj.has_pdf:
            return format_html(
                '<a href="{}" target="_blank" style="color: #10b981; font-weight: 600;">📄 PDF</a>',
                obj.pdf.arquivo.url
            )
        return format_html('<span style="color: #9ca3af;">-</span>')
    pdf_badge.short_description = 'PDF'
    
    def link_publico(self, obj):
        url = obj.get_public_url()
        return format_html(
            '<a href="{}" target="_blank" style="color: #3b82f6; font-weight: 600;">🔗 Abrir</a>',
            url
        )
    link_publico.short_description = 'Link Público'
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # READONLY FIELD METHODS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def link_publico_display(self, obj):
        if obj.pk:
            url = obj.get_public_url()
            return format_html(
                '<a href="{}" target="_blank" style="font-size: 14px;">{}</a><br>'
                '<button type="button" onclick="navigator.clipboard.writeText(\'{}\'); '
                'alert(\'Link copiado!\');" style="margin-top: 8px; padding: 6px 12px; '
                'background: #667eea; color: white; border: none; border-radius: 4px; '
                'cursor: pointer;">📋 Copiar Link</button>',
                url, url, url
            )
        return '-'
    link_publico_display.short_description = 'Link Público para Inspector'
    
    def pdf_download_link(self, obj):
        if obj.has_pdf:
            pdf = obj.pdf
            return format_html(
                '<strong>📄 {}</strong><br>'
                'Páginas: {} | Tamanho: {} MB<br>'
                '<a href="{}" target="_blank" style="display: inline-block; margin-top: 8px; '
                'padding: 8px 16px; background: #10b981; color: white; text-decoration: none; '
                'border-radius: 4px;">📥 Download PDF</a>',
                pdf.nome_arquivo,
                pdf.paginas,
                pdf.tamanho_mb,
                pdf.arquivo.url
            )
        return format_html('<em style="color: #9ca3af;">PDF ainda não gerado</em>')
    pdf_download_link.short_description = 'PDF Gerado'
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ACTIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @admin.action(description='🧾 Gerar/Regenerar PDF')
    def gerar_pdf_action(self, request, queryset):
        """Gera ou regenera PDF das vistorias selecionadas"""
        gerados = 0
        erros = []
        
        for inspection in queryset:
            if inspection.total_fotos == 0:
                erros.append(f"{inspection.titulo}: Sem fotos para gerar PDF")
                continue
            
            try:
                # Gerar PDF
                pdf_content, total_paginas = gerar_pdf_vistoria(inspection)
                
                # Salvar PDF
                from django.utils import timezone
                filename = f"Vistoria_{inspection.locacao.numero_contrato}_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
                
                if hasattr(inspection, 'pdf') and inspection.pdf:
                    pdf_obj = inspection.pdf
                    pdf_obj.arquivo.delete()
                    pdf_obj.arquivo.save(filename, pdf_content, save=False)
                    pdf_obj.paginas = total_paginas
                    pdf_obj.tamanho_bytes = pdf_content.size
                    pdf_obj.save()
                else:
                    pdf_obj = InspectionPDF(
                        inspection=inspection,
                        paginas=total_paginas,
                        tamanho_bytes=pdf_content.size
                    )
                    pdf_obj.arquivo.save(filename, pdf_content, save=True)
                
                gerados += 1
                
            except Exception as e:
                erros.append(f"{inspection.titulo}: {str(e)}")
        
        if gerados > 0:
            self.message_user(
                request,
                f"✅ {gerados} PDF(s) gerado(s) com sucesso!",
                level=messages.SUCCESS
            )
        
        if erros:
            self.message_user(
                request,
                f"⚠️ Erros: {'; '.join(erros[:3])}",
                level=messages.WARNING
            )
    
    @admin.action(description='🔄 Renovar Token (7 dias)')
    def renovar_token_action(self, request, queryset):
        """Renova token de acesso das vistorias"""
        renovados = 0
        
        for inspection in queryset:
            inspection.renovar_token(dias=7)
            renovados += 1
        
        self.message_user(
            request,
            f"✅ {renovados} token(s) renovado(s) por 7 dias!",
            level=messages.SUCCESS
        )
    
    @admin.action(description='📧 Enviar PDF por Email')
    def enviar_por_email_action(self, request, queryset):
        """Envia PDF por email para proprietário e locatário"""
        from django.core.mail import EmailMessage
        from django.template.loader import render_to_string
        
        enviados = 0
        erros = []
        
        for inspection in queryset:
            if not inspection.has_pdf:
                erros.append(f"{inspection.titulo}: PDF não gerado")
                continue
            
            locacao = inspection.locacao
            destinatarios = []
            
            # Email proprietário
            if locacao.proprietario.email:
                destinatarios.append({
                    'email': locacao.proprietario.email,
                    'nome': locacao.proprietario.nome_razao_social
                })
            
            # Email locatário
            if locacao.locatario.email:
                destinatarios.append({
                    'email': locacao.locatario.email,
                    'nome': locacao.locatario.nome_razao_social
                })
            
            for dest in destinatarios:
                try:
                    # Criar email
                    assunto = f"Relatório de Vistoria - {inspection.titulo}"
                    
                    mensagem = f"""
Olá {dest['nome']},

Segue em anexo o relatório de vistoria do imóvel:

Contrato: {locacao.numero_contrato}
Imóvel: {locacao.imovel.endereco}, {locacao.imovel.numero}
Vistoria: {inspection.titulo}
Data: {inspection.completed_at.strftime('%d/%m/%Y %H:%M') if inspection.completed_at else 'N/A'}

Páginas: {inspection.pdf.paginas}
Tamanho: {inspection.pdf.tamanho_mb} MB

---
HABITAT PRO - Sistema de Gestão de Locações
Policorp Imóveis | Paranaguá - PR
                    """
                    
                    email = EmailMessage(
                        subject=assunto,
                        body=mensagem,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[dest['email']]
                    )
                    
                    # Anexar PDF
                    inspection.pdf.arquivo.open('rb')
                    pdf_content = inspection.pdf.arquivo.read()
                    inspection.pdf.arquivo.close()
                    
                    email.attach(
                        filename=f"Vistoria_{locacao.numero_contrato}.pdf",
                        content=pdf_content,
                        mimetype='application/pdf'
                    )
                    
                    email.send()
                    enviados += 1
                    
                except Exception as e:
                    erros.append(f"{dest['nome']}: {str(e)}")
        
        if enviados > 0:
            self.message_user(
                request,
                f"✅ {enviados} email(s) enviado(s) com sucesso!",
                level=messages.SUCCESS
            )
        
        if erros:
            self.message_user(
                request,
                f"⚠️ Erros: {'; '.join(erros[:3])}",
                level=messages.WARNING
            )
    
    @admin.action(description='💬 Enviar por WhatsApp')
    def enviar_por_whatsapp_action(self, request, queryset):
        """Prepara mensagens WhatsApp com link do PDF"""
        mensagens = []
        
        for inspection in queryset:
            if not inspection.has_pdf:
                continue
            
            locacao = inspection.locacao
            imovel = locacao.imovel
            pdf_url = inspection.pdf.get_presigned_url()
            
            # Mensagem para proprietário
            if locacao.proprietario.celular:
                msg = f"""🏠 *HABITAT PRO*
📋 *RELATÓRIO DE VISTORIA*

Olá *{locacao.proprietario.nome_razao_social}*,

Segue o relatório de vistoria do imóvel:

📍 *Imóvel:* {imovel.endereco}, {imovel.numero}
🏘️ *Bairro:* {imovel.bairro}
📋 *Contrato:* {locacao.numero_contrato}

📝 *Vistoria:* {inspection.titulo}
👤 *Inspector:* {inspection.inspector_nome or 'N/A'}
📅 *Data:* {inspection.completed_at.strftime('%d/%m/%Y às %H:%M') if inspection.completed_at else 'N/A'}

📊 *Páginas:* {inspection.pdf.paginas}
💾 *Tamanho:* {inspection.pdf.tamanho_mb} MB

━━━━━━━━━━━━━━━━━━━━━━
📥 *BAIXAR RELATÓRIO (PDF)*
{pdf_url}
━━━━━━━━━━━━━━━━━━━━━━

ℹ️ Este documento registra o estado do imóvel na data indicada.

_Mensagem automática do HABITAT PRO_"""
                
                mensagens.append({
                    'nome': locacao.proprietario.nome_razao_social,
                    'telefone': locacao.proprietario.celular,
                    'mensagem': msg
                })
            
            # Mensagem para locatário
            if locacao.locatario.celular:
                msg = f"""🏠 *HABITAT PRO*
📋 *RELATÓRIO DE VISTORIA*

Olá *{locacao.locatario.nome_razao_social}*,

Segue o relatório de vistoria do imóvel:

📍 *Imóvel:* {imovel.endereco}, {imovel.numero}
🏘️ *Bairro:* {imovel.bairro}
📋 *Contrato:* {locacao.numero_contrato}

📝 *Vistoria:* {inspection.titulo}
👤 *Inspector:* {inspection.inspector_nome or 'N/A'}
📅 *Data:* {inspection.completed_at.strftime('%d/%m/%Y às %H:%M') if inspection.completed_at else 'N/A'}

📊 *Páginas:* {inspection.pdf.paginas}
💾 *Tamanho:* {inspection.pdf.tamanho_mb} MB

━━━━━━━━━━━━━━━━━━━━━━
📥 *BAIXAR RELATÓRIO (PDF)*
{pdf_url}
━━━━━━━━━━━━━━━━━━━━━━

ℹ️ Este documento registra o estado do imóvel na data indicada.

_Mensagem automática do HABITAT PRO_"""
                
                mensagens.append({
                    'nome': locacao.locatario.nome_razao_social,
                    'telefone': locacao.locatario.celular,
                    'mensagem': msg
                })
        
        return render(request, 'admin/whatsapp_vistorias.html', {
            'mensagens': mensagens,
            'total': len(mensagens)
        })


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHOTO ADMIN (opcional - apenas para debug)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@admin.register(InspectionPhoto)
class InspectionPhotoAdmin(admin.ModelAdmin):
    """Admin para fotos (apenas visualização/debug)"""
    list_display = ('inspection', 'ordem', 'legenda', 'tamanho_mb', 'tirada_em')
    list_filter = ('inspection__status', 'tirada_em')
    search_fields = ('inspection__titulo', 'legenda')
    readonly_fields = ('largura', 'altura', 'tamanho_bytes', 'tirada_em')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PDF ADMIN (opcional - apenas para debug)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@admin.register(InspectionPDF)
class InspectionPDFAdmin(admin.ModelAdmin):
    """Admin para PDFs (apenas visualização/debug)"""
    list_display = ('inspection', 'nome_arquivo', 'paginas', 'tamanho_mb', 'gerado_em')
    list_filter = ('gerado_em',)
    search_fields = ('inspection__titulo',)
    readonly_fields = ('paginas', 'tamanho_bytes', 'gerado_em')
