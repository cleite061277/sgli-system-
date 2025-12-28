"""
Views públicas para renovação de contratos
Permite que proprietário e locatário respondam renovações via link no email
HABITAT PRO - Sistema de Gestão Imobiliária
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from core.models import RenovacaoContrato
from core.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


@csrf_protect
@require_http_methods(["GET", "POST"])
def responder_renovacao_proprietario(request, token):
    """
    Página pública para proprietário responder renovação.
    URL: /renovacao/proprietario/<token>/
    """
    
    # 1. BUSCAR RENOVAÇÃO PELO TOKEN
    renovacao = get_object_or_404(RenovacaoContrato, token_proprietario=token)
    
    # 2. VALIDAÇÕES
    if renovacao.proprietario_aprovou is not None:
        # Já respondeu
        return render(request, 'renovacao/ja_respondido.html', {
            'tipo': 'proprietario',
            'decisao': 'aprovada' if renovacao.proprietario_aprovou else 'rejeitada',
            'renovacao': renovacao,
        })
    
    if renovacao.status not in ['rascunho', 'pendente_proprietario']:
        return render(request, 'renovacao/invalido.html', {
            'mensagem': 'Esta proposta não está mais disponível para resposta.'
        })
    
    # 3. SE FOR GET: MOSTRAR PÁGINA DE DECISÃO
    if request.method == 'GET':
        
        locacao_atual = renovacao.locacao_original
        
        contexto = {
            'renovacao': renovacao,
            'locacao_atual': locacao_atual,
            'imovel': locacao_atual.imovel,
            'locatario': locacao_atual.locatario,
            'proprietario': locacao_atual.imovel.locador,
            'valor_atual': locacao_atual.valor_aluguel,
            'valor_novo': renovacao.novo_valor_aluguel,
            'aumento_percentual': renovacao.aumento_percentual,
            'diferenca_valor': renovacao.diferenca_aluguel,
            'dias_para_vencimento': renovacao.dias_para_vencimento,
        }
        
        return render(request, 'renovacao/responder_proprietario.html', contexto)
    
    # 4. SE FOR POST: PROCESSAR DECISÃO
    if request.method == 'POST':
        
        decisao = request.POST.get('decisao')  # 'aprovar' ou 'rejeitar'
        ip_address = request.META.get('REMOTE_ADDR')
        
        if decisao == 'aprovar':
            # APROVAR
            renovacao.proprietario_aprovou = True
            renovacao.data_aprovacao_proprietario = timezone.now()
            renovacao.ip_aprovacao_proprietario = ip_address
            renovacao.status = 'pendente_locatario'
            renovacao.save()
            
            # Log
            logger.info(f"✅ Proprietário aprovou renovação {renovacao.id} (IP: {ip_address})")
            
            # Enviar email ao locatário
            EmailService.notificar_locatario_renovacao(renovacao)
            
            # Página de sucesso
            return render(request, 'renovacao/sucesso_aprovacao.html', {
                'renovacao': renovacao,
                'tipo': 'proprietario'
            })
        
        elif decisao == 'rejeitar':
            # REJEITAR
            motivo = request.POST.get('motivo', '')
            
            renovacao.proprietario_aprovou = False
            renovacao.data_aprovacao_proprietario = timezone.now()
            renovacao.ip_aprovacao_proprietario = ip_address
            renovacao.status = 'recusada'
            renovacao.motivo_recusa = motivo
            renovacao.save()
            
            # Log
            logger.warning(f"❌ Proprietário rejeitou renovação {renovacao.id}")
            
            return render(request, 'renovacao/sucesso_rejeicao.html', {
                'tipo': 'proprietario',
                'renovacao': renovacao,
            })
        
        else:
            # Decisão inválida
            return render(request, 'renovacao/invalido.html', {
                'mensagem': 'Decisão inválida. Por favor, tente novamente.'
            })


@csrf_protect
@require_http_methods(["GET", "POST"])
def responder_renovacao_locatario(request, token):
    """
    Página pública para locatário responder renovação.
    URL: /renovacao/locatario/<token>/
    """
    
    # 1. BUSCAR RENOVAÇÃO PELO TOKEN
    renovacao = get_object_or_404(RenovacaoContrato, token_locatario=token)
    
    # 2. VALIDAÇÕES
    if renovacao.locatario_aprovou is not None:
        # Já respondeu
        return render(request, 'renovacao/ja_respondido.html', {
            'tipo': 'locatario',
            'decisao': 'aprovada' if renovacao.locatario_aprovou else 'rejeitada',
            'renovacao': renovacao,
        })
    
    if renovacao.status != 'pendente_locatario':
        return render(request, 'renovacao/invalido.html', {
            'mensagem': 'Esta proposta ainda não está disponível para você ou já foi processada.'
        })
    
    # 3. SE FOR GET: MOSTRAR PÁGINA DE DECISÃO
    if request.method == 'GET':
        
        locacao_atual = renovacao.locacao_original
        
        # Calcular caução se aplicável
        caucao_info = None
        if renovacao.novo_tipo_garantia == 'caucao':
            nova_caucao = renovacao.calcular_nova_caucao()
            caucao_atual = locacao_atual.caucao_valor_total or 0
            caucao_info = {
                'atual': caucao_atual,
                'nova': nova_caucao,
                'diferenca': nova_caucao - caucao_atual,
            }
        
        contexto = {
            'renovacao': renovacao,
            'locacao_atual': locacao_atual,
            'imovel': locacao_atual.imovel,
            'locatario': locacao_atual.locatario,
            'proprietario': locacao_atual.imovel.locador,
            'valor_atual': locacao_atual.valor_aluguel,
            'valor_novo': renovacao.novo_valor_aluguel,
            'aumento_percentual': renovacao.aumento_percentual,
            'diferenca_valor': renovacao.diferenca_aluguel,
            'caucao_info': caucao_info,
        }
        
        return render(request, 'renovacao/responder_locatario.html', contexto)
    
    # 4. SE FOR POST: PROCESSAR DECISÃO
    if request.method == 'POST':
        
        decisao = request.POST.get('decisao')  # 'aceitar' ou 'recusar'
        ip_address = request.META.get('REMOTE_ADDR')
        
        if decisao == 'aceitar':
            # ACEITAR
            renovacao.locatario_aprovou = True
            renovacao.data_aprovacao_locatario = timezone.now()
            renovacao.ip_aprovacao_locatario = ip_address
            renovacao.status = 'aprovada'
            renovacao.save()
            
            # Log
            logger.info(f"✅ Locatário aceitou renovação {renovacao.id} (IP: {ip_address})")
            
            # Página de sucesso
            return render(request, 'renovacao/sucesso_aprovacao.html', {
                'renovacao': renovacao,
                'tipo': 'locatario'
            })
        
        elif decisao == 'recusar':
            # RECUSAR
            motivo = request.POST.get('motivo', '')
            
            renovacao.locatario_aprovou = False
            renovacao.data_aprovacao_locatario = timezone.now()
            renovacao.ip_aprovacao_locatario = ip_address
            renovacao.status = 'recusada'
            if motivo:
                renovacao.motivo_recusa = f"Locatário: {motivo}"
            renovacao.save()
            
            # Log
            logger.warning(f"❌ Locatário recusou renovação {renovacao.id}")
            
            return render(request, 'renovacao/sucesso_rejeicao.html', {
                'tipo': 'locatario',
                'renovacao': renovacao,
            })
        
        else:
            # Decisão inválida
            return render(request, 'renovacao/invalido.html', {
                'mensagem': 'Decisão inválida. Por favor, tente novamente.'
            })
