"""
Admin actions para gerenciamento de tokens públicos
DEV_21.6 - Fase 3
"""
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from core.utils.token_publico import renovar_token, gerar_url_publica


def action_reenviar_link_comanda(modeladmin, request, queryset):
    """
    Action para reenviar link público da comanda por email.
    """
    enviados = 0
    erros = 0
    
    for comanda in queryset:
        try:
            # Gerar URL pública
            url = gerar_url_publica(comanda, 'comanda')
            
            # Verificar se tem email
            if not comanda.locacao or not comanda.locacao.locatario.email:
                messages.warning(
                    request,
                    f"Comanda {comanda.numero_comanda}: Locatário sem email cadastrado"
                )
                continue
            
            # Enviar email
            assunto = f"Link da Comanda {comanda.numero_comanda} - HABITAT PRO"
            mensagem = f"""
Olá {comanda.locacao.locatario.nome_razao_social},

Segue o link para visualizar sua comanda de aluguel:

🔗 {url}

⏰ Este link é válido por 30 dias.

Imóvel: {comanda.locacao.imovel.endereco}, {comanda.locacao.imovel.numero}
Vencimento: {comanda.data_vencimento.strftime('%d/%m/%Y')}
Valor: R$ {comanda.valor_total:,.2f}

---
HABITAT PRO
Sistema de Gestão Imobiliária
            """
            
            send_mail(
                assunto,
                mensagem,
                settings.DEFAULT_FROM_EMAIL,
                [comanda.locacao.locatario.email],
                fail_silently=False,
            )
            
            enviados += 1
            
        except Exception as e:
            erros += 1
            messages.error(
                request,
                f"Erro ao enviar email da comanda {comanda.numero_comanda}: {str(e)}"
            )
    
    # Mensagem de sucesso
    if enviados > 0:
        messages.success(
            request,
            f"✅ {enviados} link(s) reenviado(s) com sucesso!"
        )
    if erros > 0:
        messages.error(
            request,
            f"❌ {erros} erro(s) ao enviar emails"
        )

action_reenviar_link_comanda.short_description = "📧 Reenviar link público por email"


def action_renovar_token_comanda(modeladmin, request, queryset):
    """
    Action para renovar token (gerar novo) de comandas.
    """
    renovados = 0
    
    for comanda in queryset:
        renovar_token(comanda, salvar=True)
        renovados += 1
    
    messages.success(
        request,
        f"✅ {renovados} token(s) renovado(s)! Novos links válidos por 30 dias."
    )

action_renovar_token_comanda.short_description = "🔄 Renovar tokens (gerar novos)"


def action_reenviar_link_recibo(modeladmin, request, queryset):
    """
    Action para reenviar link público do recibo por email.
    """
    enviados = 0
    erros = 0
    
    for pagamento in queryset:
        try:
            # Gerar URL pública
            url = gerar_url_publica(pagamento, 'recibo')
            
            # Verificar se tem email
            if not pagamento.comanda or not pagamento.comanda.locacao or not pagamento.comanda.locacao.locatario.email:
                messages.warning(
                    request,
                    f"Recibo {pagamento.numero_pagamento}: Locatário sem email cadastrado"
                )
                continue
            
            # Enviar email
            assunto = f"Recibo de Pagamento {pagamento.numero_pagamento} - HABITAT PRO"
            mensagem = f"""
Olá {pagamento.comanda.locacao.locatario.nome_razao_social},

Segue o link para visualizar seu recibo de pagamento:

🔗 {url}

⏰ Este link é válido por 30 dias.

Recibo: {pagamento.numero_pagamento}
Data Pagamento: {pagamento.data_pagamento.strftime('%d/%m/%Y')}
Valor Pago: R$ {pagamento.valor_pago:,.2f}

---
HABITAT PRO
Sistema de Gestão Imobiliária
            """
            
            send_mail(
                assunto,
                mensagem,
                settings.DEFAULT_FROM_EMAIL,
                [pagamento.comanda.locacao.locatario.email],
                fail_silently=False,
            )
            
            enviados += 1
            
        except Exception as e:
            erros += 1
            messages.error(
                request,
                f"Erro ao enviar email do recibo {pagamento.numero_pagamento}: {str(e)}"
            )
    
    # Mensagem de sucesso
    if enviados > 0:
        messages.success(
            request,
            f"✅ {enviados} link(s) reenviado(s) com sucesso!"
        )
    if erros > 0:
        messages.error(
            request,
            f"❌ {erros} erro(s) ao enviar emails"
        )

action_reenviar_link_recibo.short_description = "📧 Reenviar link público por email"


def action_renovar_token_recibo(modeladmin, request, queryset):
    """
    Action para renovar token (gerar novo) de recibos.
    """
    renovados = 0
    
    for pagamento in queryset:
        renovar_token(pagamento, salvar=True)
        renovados += 1
    
    messages.success(
        request,
        f"✅ {renovados} token(s) renovado(s)! Novos links válidos por 30 dias."
    )

action_renovar_token_recibo.short_description = "🔄 Renovar tokens (gerar novos)"


def action_renovar_token_renovacao(modeladmin, request, queryset):
    """
    Action para renovar tokens de renovações de contrato.
    Renova AMBOS: token_proprietario E token_locatario
    """
    from django.contrib import messages
    from core.utils.token_publico import renovar_token
    
    renovados = 0
    
    for renovacao in queryset:
        # Renovar ambos os tokens
        try:
            # Token proprietário
            if hasattr(renovacao, 'token_proprietario'):
                renovacao.token_expira_em = timezone.now() + timedelta(days=30)
            
            # Token locatário  
            if hasattr(renovacao, 'token_locatario'):
                renovacao.token_locatario_expira_em = timezone.now() + timedelta(days=30)
            
            renovacao.save()
            renovados += 1
        except Exception as e:
            messages.error(request, f"Erro ao renovar tokens: {e}")
    
    if renovados > 0:
        messages.success(
            request,
            f"✅ {renovados} renovação(ões) com tokens atualizados! Novos links válidos por 30 dias."
        )

action_renovar_token_renovacao.short_description = "🔄 Renovar tokens (proprietário + locatário)"


# ═══════════════════════════════════════════════════════════════
# ACTIONS PARA RENOVAÇÕES - REENVIO POR EMAIL
# ═══════════════════════════════════════════════════════════════

def action_reenviar_link_renovacao_proprietario(modeladmin, request, queryset):
    """
    Action para reenviar link de renovação para PROPRIETÁRIO por email.
    """
    from django.contrib import messages
    from django.core.mail import send_mail
    from django.conf import settings
    from core.utils.token_publico import gerar_url_publica
    
    enviados = 0
    erros = 0
    
    for renovacao in queryset:
        try:
            # Validar email do proprietário
            if not renovacao.locacao_original or not renovacao.locacao_original.imovel.locador.email:
                messages.warning(
                    request,
                    f"Renovação {renovacao.id}: Proprietário sem email"
                )
                continue
            
            # Gerar URL usando token_proprietario
            url = gerar_url_publica(renovacao, 'renovacao', tipo_pessoa='proprietario')
            
            # Enviar email
            email_destino = renovacao.locacao_original.imovel.locador.email
            nome_proprietario = renovacao.locacao_original.imovel.locador.nome_razao_social
            codigo_imovel = renovacao.locacao_original.imovel.codigo_imovel
            
            assunto = f"Proposta de Renovação de Contrato - {codigo_imovel}"
            
            mensagem = f"""
Prezado(a) {nome_proprietario},

Você tem uma proposta de renovação de contrato para análise.

🏠 Imóvel: {codigo_imovel}
📋 Locação: {renovacao.locacao_original.numero_contrato}

Acesse o link abaixo para visualizar a proposta e responder:

🔗 {url}

⏰ Este link é válido por 30 dias.

---
HABITAT PRO
Sistema de Gestão Imobiliária
            """
            
            send_mail(
                assunto,
                mensagem,
                settings.DEFAULT_FROM_EMAIL,
                [email_destino],
                fail_silently=False,
            )
            
            enviados += 1
            
        except Exception as e:
            erros += 1
            messages.error(
                request,
                f"Erro ao enviar email da renovação {renovacao.id}: {str(e)}"
            )
    
    # Mensagem de sucesso
    if enviados > 0:
        messages.success(
            request,
            f"✅ {enviados} link(s) reenviado(s) para proprietário(s)!"
        )
    if erros > 0:
        messages.error(
            request,
            f"❌ {erros} erro(s) ao enviar emails"
        )

action_reenviar_link_renovacao_proprietario.short_description = "📧 Reenviar link - Proprietário"


def action_reenviar_link_renovacao_locatario(modeladmin, request, queryset):
    """
    Action para reenviar link de renovação para LOCATÁRIO por email.
    """
    from django.contrib import messages
    from django.core.mail import send_mail
    from django.conf import settings
    from core.utils.token_publico import gerar_url_publica
    
    enviados = 0
    erros = 0
    
    for renovacao in queryset:
        try:
            # Validar email do locatário
            if not renovacao.locacao_original or not renovacao.locacao_original.locatario.email:
                messages.warning(
                    request,
                    f"Renovação {renovacao.id}: Locatário sem email"
                )
                continue
            
            # Gerar URL usando token_locatario
            url = gerar_url_publica(renovacao, 'renovacao', tipo_pessoa='locatario')
            
            # Enviar email
            email_destino = renovacao.locacao_original.locatario.email
            nome_locatario = renovacao.locacao_original.locatario.nome_razao_social
            codigo_imovel = renovacao.locacao_original.imovel.codigo_imovel
            
            assunto = f"Proposta de Renovação de Contrato - {codigo_imovel}"
            
            mensagem = f"""
Prezado(a) {nome_locatario},

Você tem uma proposta de renovação de contrato para análise.

🏠 Imóvel: {codigo_imovel}
📋 Locação: {renovacao.locacao_original.numero_contrato}

Acesse o link abaixo para visualizar a proposta e responder:

🔗 {url}

⏰ Este link é válido por 30 dias.

---
HABITAT PRO
Sistema de Gestão Imobiliária
            """
            
            send_mail(
                assunto,
                mensagem,
                settings.DEFAULT_FROM_EMAIL,
                [email_destino],
                fail_silently=False,
            )
            
            enviados += 1
            
        except Exception as e:
            erros += 1
            messages.error(
                request,
                f"Erro ao enviar email da renovação {renovacao.id}: {str(e)}"
            )
    
    # Mensagem de sucesso
    if enviados > 0:
        messages.success(
            request,
            f"✅ {enviados} link(s) reenviado(s) para locatário(s)!"
        )
    if erros > 0:
        messages.error(
            request,
            f"❌ {erros} erro(s) ao enviar emails"
        )

action_reenviar_link_renovacao_locatario.short_description = "📧 Reenviar link - Locatário"
