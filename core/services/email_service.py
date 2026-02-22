"""
Serviço responsável pelo envio de emails de notificação.
Princípios: Single Responsibility, Testável, Reutilizável
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from core.models import LogNotificacao, Comanda
from datetime import date
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Serviço de envio de emails de notificação"""
    
    TIPOS_MENSAGEM = {
        '10D': {
            'titulo': 'Lembrete: Vencimento em 10 dias',
            'mensagem': 'Seu aluguel vence em 10 dias. Não esqueça de efetuar o pagamento.',
        },
        '7D': {
            'titulo': 'Lembrete: Vencimento em 7 dias',
            'mensagem': 'Seu aluguel vence em 7 dias. Por favor, organize o pagamento.',
        },
        '1D': {
            'titulo': 'Lembrete: Vencimento AMANHÃ',
            'mensagem': 'Seu aluguel vence AMANHÃ. Por favor, efetue o pagamento para evitar multa e juros.',
        },
        'VEN': {
            'titulo': 'Lembrete: Vencimento HOJE',
            'mensagem': 'Seu aluguel vence HOJE. Efetue o pagamento para evitar multa de 10% e juros de 1% ao mês.',
        },
        'ATR1': {
            'titulo': '⚠️ PAGAMENTO EM ATRASO',
            'mensagem': 'Seu aluguel está em atraso há 1 dia. Multa de 10% e juros já foram aplicados.',
        },
        'ATR7': {
            'titulo': '⚠️ PAGAMENTO EM ATRASO - 7 dias',
            'mensagem': 'Seu aluguel está em atraso há 7 dias. Por favor, regularize sua situação.',
        },
        'ATR14': {
            'titulo': '⚠️ PAGAMENTO EM ATRASO - 14 dias',
            'mensagem': 'Seu aluguel está em atraso há 14 dias. Entre em contato urgentemente.',
        },
        'ATR21': {
            'titulo': '⚠️ PAGAMENTO EM ATRASO - 21 dias',
            'mensagem': 'Seu aluguel está em atraso há 21 dias. Situação crítica. Entre em contato imediatamente.',
        },
    }
    
    @staticmethod
    def preparar_contexto(comanda: Comanda, tipo_notificacao: str) -> dict:
        """Prepara contexto para renderizar template"""
        
        # Aplicar multa/juros se vencida
        if comanda.is_vencida:
            comanda.aplicar_multa_juros(salvar=True)
            comanda.refresh_from_db()
        
        config = EmailService.TIPOS_MENSAGEM[tipo_notificacao]
        
        return {
            'titulo': config['titulo'],
            'mensagem_principal': config['mensagem'],
            'locatario_nome': comanda.locacao.locatario.nome_razao_social,
            'imovel_endereco': f"{comanda.locacao.imovel.endereco}, {comanda.locacao.imovel.numero}",
            'numero_comanda': comanda.numero_comanda,
            'data_vencimento': comanda.data_vencimento.strftime('%d/%m/%Y'),
            'valor_aluguel': f"{comanda.valor_aluguel:,.2f}",
            'valor_condominio': f"{comanda.valor_condominio:,.2f}",
            'valor_iptu': f"{comanda.valor_iptu:,.2f}",
            'valor_multa': f"{comanda.valor_multa:,.2f}",
            'valor_juros': f"{comanda.valor_juros:,.2f}",
            'valor_total': f"{comanda.valor_total:,.2f}",
            'tem_multa_juros': comanda.is_vencida,
            'dias_atraso': comanda.dias_atraso if comanda.is_vencida else 0,
            'link_pagamento': f"http://localhost:8000/admin/core/comanda/{comanda.id}/change/",
        }
    
    @classmethod
    def enviar_notificacao(cls, comanda: Comanda, tipo_notificacao: str) -> bool:
        """
        Envia email de notificação para locatário
        """
        try:
            # Validações
            if not comanda.locacao.locatario.email:
                logger.warning(f"Comanda {comanda.numero_comanda}: Locatário sem email")
                return False
            
            # Preparar contexto
            contexto = cls.preparar_contexto(comanda, tipo_notificacao)
            
            # Renderizar templates
            html_content = render_to_string('emails/lembrete_vencimento.html', contexto)
            text_content = render_to_string('emails/lembrete_vencimento.txt', contexto)
            
            # Criar email
            email = EmailMultiAlternatives(
                subject=contexto['titulo'],
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[comanda.locacao.locatario.email],
            )
            email.attach_alternative(html_content, "text/html")
            
            # Enviar
            email.send()
            
            # Registrar log
            LogNotificacao.objects.create(
                comanda=comanda,
                tipo_notificacao=tipo_notificacao,
                destinatario_email=comanda.locacao.locatario.email,
                sucesso=True
            )
            
            logger.info(f"✅ Email enviado: {tipo_notificacao} - {comanda.numero_comanda}")
            return True
            
        except Exception as e:
            LogNotificacao.objects.create(
                comanda=comanda,
                tipo_notificacao=tipo_notificacao,
                destinatario_email=comanda.locacao.locatario.email or 'sem_email@erro.com',
                sucesso=False,
                mensagem_erro=str(e)
            )
            
            logger.error(f"❌ Erro ao enviar email: {comanda.numero_comanda} - {e}")
            return False

    # ════════════════════════════════════════════════════════════════════
    # MÉTODOS PARA RENOVAÇÃO DE CONTRATOS - DEV_21
    # ════════════════════════════════════════════════════════════════════
    
    @classmethod
    def notificar_admin_nova_renovacao(cls, renovacao):
        """
        Notifica administrador sobre nova renovação detectada.
        
        Args:
            renovacao: Objeto RenovacaoContrato
        """
        from django.core.mail import send_mail
        from django.utils.html import strip_tags
        
        locacao_atual = renovacao.locacao_original
        
        assunto = f'🔄 Nova Renovação Detectada - {locacao_atual.imovel.endereco_completo}'
        
        mensagem_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 30px; text-align: center;">
                <h1 style="margin: 0;">🏠 HABITAT PRO</h1>
                <p style="margin: 10px 0 0 0;">Nova Renovação Detectada</p>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h3>📋 Contrato Atual:</h3>
                <ul style="line-height: 1.8;">
                    <li><strong>Imóvel:</strong> {locacao_atual.imovel.endereco_completo}</li>
                    <li><strong>Locatário:</strong> {locacao_atual.locatario.nome_razao_social}</li>
                    <li><strong>Vencimento:</strong> {locacao_atual.data_fim.strftime('%d/%m/%Y')} 
                        ({renovacao.dias_para_vencimento} dias)</li>
                    <li><strong>Valor atual:</strong> R$ {locacao_atual.valor_aluguel:,.2f}</li>
                </ul>
                
                <h3>💡 Proposta Criada:</h3>
                <ul style="line-height: 1.8;">
                    <li><strong>Nova vigência:</strong> {renovacao.nova_data_inicio.strftime('%d/%m/%Y')} 
                        a {renovacao.nova_data_fim.strftime('%d/%m/%Y')}</li>
                    <li><strong>Valor proposto:</strong> R$ {renovacao.novo_valor_aluguel:,.2f}</li>
                    <li><strong>Status:</strong> {renovacao.get_status_display()}</li>
                </ul>
                
                <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; 
                            margin: 20px 0; border-radius: 4px;">
                    <strong>⚠️ Ação Necessária:</strong><br>
                    Acesse o admin para revisar valores e enviar proposta ao proprietário.
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.SITE_URL}/admin/core/renovacaocontrato/{renovacao.id}/change/" 
                       style="background: #28a745; color: white; padding: 15px 40px; 
                              text-decoration: none; border-radius: 8px; font-weight: bold;
                              display: inline-block;">
                        📝 REVISAR RENOVAÇÃO
                    </a>
                </div>
            </div>
        </div>
        """
        
        try:
            send_mail(
                subject=assunto,
                message=strip_tags(mensagem_html),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMINS[0][1] if settings.ADMINS else 'admin@aec.com.br'],
                html_message=mensagem_html,
                fail_silently=False,
            )
            logger.info(f"✅ Email enviado ao admin - Nova renovação {renovacao.id}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email ao admin: {e}")
            return False
    
    @classmethod
    def notificar_proprietario_renovacao(cls, renovacao):
        """
        Notifica proprietário sobre proposta de renovação com link para responder.
        
        Args:
            renovacao: Objeto RenovacaoContrato
        """
        from django.core.mail import send_mail
        from django.utils.html import strip_tags
        
        import logging
        import traceback
        
        logger = logging.getLogger(__name__)
        
        try:
            
            locacao_atual = renovacao.locacao_original
        except Exception as e:
            logger.error(f"❌ ERRO NO DEBUG: {e}")
            logger.error(f"TRACEBACK: {traceback.format_exc()}")
            raise
        
        locacao_atual = renovacao.locacao_original
        proprietario = locacao_atual.imovel.locador
        
        # Gerar URL completa
        base_url = settings.SITE_URL
        url_responder = f"{base_url}/renovacao/proprietario/{renovacao.token_proprietario}/"
        
        assunto = f'Proposta de Renovação - {locacao_atual.imovel.endereco_completo}'
        
        aumento = renovacao.aumento_percentual
        
        mensagem_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 30px; text-align: center;">
                <h1 style="margin: 0;">🏠 HABITAT PRO</h1>
                <p style="margin: 10px 0 0 0;">Proposta de Renovação</p>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <p>Olá <strong>{proprietario.nome_razao_social}</strong>,</p>
                
                <p>O contrato do imóvel <strong>{locacao_atual.imovel.endereco_completo}</strong> 
                vence em {renovacao.dias_para_vencimento} dias.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">📋 Proposta de Renovação:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #dee2e6;">
                            <td style="padding: 10px;"><strong>Locatário:</strong></td>
                            <td style="padding: 10px;">{locacao_atual.locatario.nome_razao_social}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dee2e6;">
                            <td style="padding: 10px;"><strong>Valor atual:</strong></td>
                            <td style="padding: 10px;">R$ {locacao_atual.valor_aluguel:,.2f}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dee2e6;">
                            <td style="padding: 10px;"><strong>Valor novo:</strong></td>
                            <td style="padding: 10px;">
                                <strong style="color: #28a745;">R$ {renovacao.novo_valor_aluguel:,.2f}</strong>
                                <span style="color: #666; font-size: 12px;">
                                    ({'+' if aumento >= 0 else ''}{aumento:.1f}%)
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 10px;"><strong>Vigência:</strong></td>
                            <td style="padding: 10px;">
                                {renovacao.nova_data_inicio.strftime('%d/%m/%Y')} a 
                                {renovacao.nova_data_fim.strftime('%d/%m/%Y')}
                            </td>
                        </tr>
                    </table>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{url_responder}" 
                       style="background: #28a745; color: white; padding: 15px 40px; 
                              text-decoration: none; border-radius: 8px; font-weight: bold;
                              display: inline-block; font-size: 16px;">
                        📝 RESPONDER AGORA
                    </a>
                </div>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    ⏰ <strong>Prazo:</strong> 15 dias para resposta<br>
                    🔒 Link seguro e exclusivo para você
                </p>
            </div>
            
            <div style="background: #333; color: white; padding: 20px; 
                        text-align: center; font-size: 12px;">
                Dúvidas? Entre em contato através do sistema.<br>
                <strong>HABITAT PRO - A&C Imóveis e Sistemas Imobiliários</strong>
            </div>
        </div>
        """
        
        try:
            send_mail(
                subject=assunto,
                message=strip_tags(mensagem_html),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[proprietario.email],
                html_message=mensagem_html,
                fail_silently=False,
            )
            
            # Registrar comunicação
            renovacao.registrar_comunicacao('email', 'proprietario', True, 
                                           f'Email enviado para {proprietario.email}')
            
            logger.info(f"✅ Email enviado ao proprietário - Renovação {renovacao.id}")
            return True
        except Exception as e:
            renovacao.registrar_comunicacao('email', 'proprietario', False, str(e))
            logger.error(f"❌ Erro ao enviar email ao proprietário: {e}")
            return False
    
    @classmethod
    def notificar_locatario_renovacao(cls, renovacao):
        """
        Notifica locatário sobre proposta de renovação aprovada pelo proprietário.
        
        Args:
            renovacao: Objeto RenovacaoContrato
        """
        from django.core.mail import send_mail
        from django.utils.html import strip_tags
        
        locacao_atual = renovacao.locacao_original
        locatario = locacao_atual.locatario
        
        # Gerar URL completa
        base_url = settings.SITE_URL
        url_responder = f"{base_url}/renovacao/locatario/{renovacao.token_locatario}/"
        
        assunto = f'Proposta de Renovação Aprovada - {locacao_atual.imovel.endereco_completo}'
        
        aumento = renovacao.aumento_percentual
        diferenca = renovacao.diferenca_aluguel
        
        mensagem_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 30px; text-align: center;">
                <h1 style="margin: 0;">🏠 HABITAT PRO</h1>
                <p style="margin: 10px 0 0 0;">Proposta de Renovação</p>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <p>Olá <strong>{locatario.nome_razao_social}</strong>,</p>
                
                <p>Seu contrato do imóvel <strong>{locacao_atual.imovel.endereco_completo}</strong> 
                foi aprovado para renovação!</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">📋 Proposta de Renovação:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #dee2e6;">
                            <td style="padding: 10px;"><strong>Valor atual:</strong></td>
                            <td style="padding: 10px;">R$ {locacao_atual.valor_aluguel:,.2f}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dee2e6;">
                            <td style="padding: 10px;"><strong>Valor novo:</strong></td>
                            <td style="padding: 10px;">
                                <strong style="color: #28a745;">R$ {renovacao.novo_valor_aluguel:,.2f}</strong>
                                <span style="color: #666; font-size: 12px;">
                                    ({'+' if aumento >= 0 else ''}{aumento:.1f}%)
                                </span>
                            </td>
                        </tr>
                        <tr style="border-bottom: 1px solid #dee2e6;">
                            <td style="padding: 10px;"><strong>Diferença mensal:</strong></td>
                            <td style="padding: 10px;">
                                R$ {diferenca:,.2f}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 10px;"><strong>Vigência:</strong></td>
                            <td style="padding: 10px;">
                                {renovacao.nova_data_inicio.strftime('%d/%m/%Y')} a 
                                {renovacao.nova_data_fim.strftime('%d/%m/%Y')}
                            </td>
                        </tr>
                    </table>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{url_responder}" 
                       style="background: #28a745; color: white; padding: 15px 40px; 
                              text-decoration: none; border-radius: 8px; font-weight: bold;
                              display: inline-block; font-size: 16px;">
                        📝 ACEITAR OU RECUSAR
                    </a>
                </div>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    ⏰ <strong>Prazo:</strong> 30 dias para resposta<br>
                    🔒 Link seguro e exclusivo para você
                </p>
            </div>
            
            <div style="background: #333; color: white; padding: 20px; 
                        text-align: center; font-size: 12px;">
                Dúvidas? Entre em contato através do sistema.<br>
                <strong>HABITAT PRO - A&C Imóveis e Sistemas Imobiliários</strong>
            </div>
        </div>
        """
        
        try:
            send_mail(
                subject=assunto,
                message=strip_tags(mensagem_html),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[locatario.email],
                html_message=mensagem_html,
                fail_silently=False,
            )
            
            # Registrar comunicação
            renovacao.registrar_comunicacao('email', 'locatario', True, 
                                           f'Email enviado para {locatario.email}')
            
            logger.info(f"✅ Email enviado ao locatário - Renovação {renovacao.id}")
            return True
        except Exception as e:
            renovacao.registrar_comunicacao('email', 'locatario', False, str(e))
            logger.error(f"❌ Erro ao enviar email ao locatário: {e}")
            return False
            
            # ────────────────────────────────────────────────────────────────
# MÉTODOS PARA RESCISÃO DE CONTRATOS
# ────────────────────────────────────────────────────────────────

    @classmethod
    def enviar_confirmacao_rescisao(cls, rescisao):
        """
        Envia email com link de confirmação para inquilino.
        Similar ao envio de renovação de contratos.
        """
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            locatario = rescisao.locacao.locatario
            
            if not locatario.email:
                logger.warning(f"Rescisão {rescisao.id}: Locatário sem email")
                return False
            
            # Gerar link de confirmação
            link_confirmacao = rescisao.token_confirmacao
            url_confirmacao = f"{settings.SITE_URL}/rescisao/confirmar/{link_confirmacao}/"
            
            # Contexto para template
            contexto = {
                'locatario_nome': locatario.nome_razao_social,
                'numero_contrato': rescisao.locacao.numero_contrato,
                'imovel_endereco': f"{rescisao.locacao.imovel.endereco}, {rescisao.locacao.imovel.numero}",
                'data_desocupacao': rescisao.data_desocupacao.strftime('%d/%m/%Y'),
                'valor_total': f"R$ {rescisao.valor_total_devido:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'quantidade_parcelas': rescisao.quantidade_parcelas,
                'valor_parcela': f"R$ {rescisao.valor_parcela:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'link_confirmacao': url_confirmacao,
                'expiracao': rescisao.token_confirmacao_expira.strftime('%d/%m/%Y') if rescisao.token_confirmacao_expira else '7 dias',
            }
            
            # Assunto
            assunto = f'🏠 Confirmação de Rescisão - Contrato {rescisao.locacao.numero_contrato}'
            
            # Corpo do email (texto simples)
            mensagem_texto = f"""
Olá {contexto['locatario_nome']},

Solicitamos a confirmação da rescisão do seu contrato de locação:

DADOS DO CONTRATO:
• Número: {contexto['numero_contrato']}
• Imóvel: {contexto['imovel_endereco']}
• Data de Desocupação: {contexto['data_desocupacao']}

VALORES:
• Total Devido: {contexto['valor_total']}
• Parcelamento: {contexto['quantidade_parcelas']}x de {contexto['valor_parcela']}

Para confirmar, acesse o link abaixo:
{contexto['link_confirmacao']}

Link válido até: {contexto['expiracao']}

Em caso de dúvidas, entre em contato conosco.

HABITAT PRO
Gestão Imobiliaria Inteligente
"""
            
            # Email HTML (se tiver template)
            try:
                mensagem_html = render_to_string('emails/confirmacao_rescisao.html', contexto)
            except:
                mensagem_html = mensagem_texto.replace('\n', '<br>')
            
            # Enviar email
            email = EmailMultiAlternatives(
                subject=assunto,
                body=mensagem_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[locatario.email]
            )
            email.attach_alternative(mensagem_html, "text/html")
            email.send()
            
            logger.info(f"✅ Email de confirmação enviado para {locatario.email}")
            
            # Registrar no log da rescisão
            rescisao.registrar_comunicacao(
                tipo='email',
                destinatario=locatario.email,
                sucesso=True,
                detalhes=f'Email de confirmação enviado - Link: {url_confirmacao}'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de confirmação: {e}")
            rescisao.registrar_comunicacao(
                tipo='email',
                destinatario=locatario.email if locatario else 'desconhecido',
                sucesso=False,
                detalhes=f'Erro: {str(e)}'
            )
            return False


    @classmethod
    def notificar_confirmacao_rescisao(cls, rescisao):
        """
        Notifica admin e locador quando inquilino confirma rescisão.
        """
        from django.conf import settings
        from django.core.mail import send_mail
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Email para admin
            assunto_admin = f'✅ Rescisão Confirmada - {rescisao.locacao.numero_contrato}'
            mensagem_admin = f"""
Rescisão confirmada pelo inquilino:

CONTRATO: {rescisao.locacao.numero_contrato}
IMÓVEL: {rescisao.locacao.imovel.endereco}
INQUILINO: {rescisao.locacao.locatario.nome_razao_social}
DATA CONFIRMAÇÃO: {rescisao.data_confirmacao_inquilino.strftime('%d/%m/%Y %H:%M') if rescisao.data_confirmacao_inquilino else 'N/A'}
CANAL: {'Link Público' if rescisao.log_confirmacao_inquilino.get('tipo') != 'confirmacao_manual' else 'Manual'}

PRÓXIMOS PASSOS:
1. Agendar vistoria
2. Calcular valores
3. Gerar documentos
4. Enviar comandas de pagamento

Acesse o admin para continuar o processo.
"""
            
            send_mail(
                subject=assunto_admin,
                message=mensagem_admin,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
            )
            
            logger.info(f"✅ Notificação de confirmação enviada ao admin")
            return True
        
        except Exception as e:
            logger.error(f"❌ Erro ao notificar confirmação: {e}")
            return False


    @classmethod
    def enviar_comanda_rescisao(cls, comanda):
        """
        Envia email com comanda de pagamento de rescisão.
        Similar ao envio de comandas de aluguel.
        """
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            locatario = comanda.get_destinatario()
            
            if not locatario.email:
                logger.warning(f"Comanda Rescisão {comanda.id}: Locatário sem email")
                return False
            
            # Link público da comanda
            link_comanda = f"{settings.SITE_URL}/comanda-rescisao/{comanda.token_publico}/"
            
            # Contexto
            contexto = {
                'locatario_nome': locatario.nome_razao_social,
                'parcela': f"{comanda.numero_parcela}/{comanda.rescisao.quantidade_parcelas}",
                'valor': comanda.valor_formatado,
                'data_vencimento': comanda.data_vencimento.strftime('%d/%m/%Y'),
                'descricao': comanda.descricao,
                'link_comanda': link_comanda,
                'dias_para_vencimento': comanda.dias_para_vencimento,
            }
            
            # Assunto
            assunto = f'💳 Parcela {contexto["parcela"]} - Rescisão Contrato'
            
            # Corpo texto
            mensagem_texto = f"""
Olá {contexto['locatario_nome']},

Segue comanda de pagamento da rescisão:

PARCELA: {contexto['parcela']}
VALOR: {contexto['valor']}
VENCIMENTO: {contexto['data_vencimento']}

Visualizar comanda:
{contexto['link_comanda']}

HABITAT PRO
Gestão Imobiliaria Inteligente
"""
            
            # Email
            email = EmailMultiAlternatives(
                subject=assunto,
                body=mensagem_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[locatario.email]
            )
            email.send()
            
            logger.info(f"✅ Comanda de rescisão enviada para {locatario.email}")
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"❌ Erro ao enviar comanda de rescisão: {e}")
            return False

    @classmethod
    def enviar_confirmacao_rescisao(cls, rescisao):
        """
        Envia email com link de confirmação para inquilino.
        """
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            locatario = rescisao.locacao.locatario
            
            if not locatario.email:
                logger.warning(f"Rescisão {rescisao.id}: Locatário sem email")
                return False
            
            # Gerar link de confirmação
            link_confirmacao = f"{settings.SITE_URL}/rescisao/confirmar/{rescisao.token_confirmacao}/"
            
            # Assunto
            assunto = f'Confirmacao de Rescisao - Contrato {rescisao.locacao.numero_contrato}'
            
            # Corpo do email (texto simples)
            mensagem_texto = f"""
Ola {locatario.nome_razao_social},

Solicitamos a confirmacao da rescisao do seu contrato de locacao:

DADOS DO CONTRATO:
- Numero: {rescisao.locacao.numero_contrato}
- Imovel: {rescisao.locacao.imovel.endereco}
- Data de Desocupacao: {rescisao.data_desocupacao.strftime('%d/%m/%Y')}

VALORES:
- Total Devido: R$ {rescisao.valor_total_devido:,.2f}
- Parcelamento: {rescisao.quantidade_parcelas}x de R$ {rescisao.valor_parcela:,.2f}

Para confirmar, acesse o link abaixo:
{link_confirmacao}

Link valido ate: {rescisao.token_confirmacao_expira.strftime('%d/%m/%Y') if rescisao.token_confirmacao_expira else '7 dias'}

Em caso de duvidas, entre em contato conosco.

HABITAT PRO
Gestao Imobiliaria Inteligente
"""
            
            # Enviar email
            email = EmailMultiAlternatives(
                subject=assunto,
                body=mensagem_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[locatario.email]
            )
            email.send()
            
            logger.info(f"✅ Email de confirmacao enviado para {locatario.email}")
            
            # Registrar no log da rescisão
            rescisao.registrar_comunicacao(
                tipo='email',
                destinatario=locatario.email,
                sucesso=True,
                detalhes=f'Email de confirmacao enviado - Link: {link_confirmacao}'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de confirmacao: {e}")
            if 'rescisao' in locals() and 'locatario' in locals():
                rescisao.registrar_comunicacao(
                    tipo='email',
                    destinatario=locatario.email if locatario else 'desconhecido',
                    sucesso=False,
                    detalhes=f'Erro: {str(e)}'
                )
            return False
    @classmethod
    def enviar_atraso_rescisao(cls, comanda):
        """
        Envia notificação de atraso de parcela de rescisão.
        """
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            locatario = comanda.get_destinatario()
            
            if not locatario.email:
                return False
            
            assunto = f'⚠️ PAGAMENTO EM ATRASO - Rescisão Contrato'
            
            mensagem_texto = f"""
Olá {locatario.nome_razao_social},

Identificamos que o pagamento da parcela {comanda.numero_parcela}/{comanda.rescisao.quantidade_parcelas} da rescisão está em atraso.

VALOR: {comanda.valor_formatado}
VENCIMENTO: {comanda.data_vencimento.strftime('%d/%m/%Y')}
DIAS DE ATRASO: {comanda.dias_atraso}

Regularize sua situação o quanto antes para evitar multa de 10% + IPCA e possível ajuizamento.

Link: {settings.SITE_URL}/comanda-rescisao/{comanda.token_publico}/

HABITAT PRO
Gestão Imobiliaria Inteligente
"""
            
            email = EmailMultiAlternatives(
                subject=assunto,
                body=mensagem_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[locatario.email]
            )
            email.send()
            
            logger.info(f"✅ Notificação de atraso enviada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar notificação de atraso: {e}")
            return False


    @classmethod
    def enviar_recibo_rescisao(cls, comanda):
        """
        Envia recibo de pagamento de parcela de rescisão.
        """
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            locatario = comanda.get_destinatario()
            
            if not locatario.email:
                return False
            
            assunto = f'✅ Recibo de Pagamento - Parcela {comanda.numero_parcela}'
            
            mensagem_texto = f"""
Olá {locatario.nome_razao_social},

Confirmamos o recebimento do pagamento:

PARCELA: {comanda.numero_parcela}/{comanda.rescisao.quantidade_parcelas}
VALOR: {comanda.valor_formatado}
DATA PAGAMENTO: {comanda.data_pagamento.strftime('%d/%m/%Y')}

Obrigado!

Atenciosamente,
HABITAT PRO
Gestão Imobiliaria Inteligente
"""
            
            email = EmailMultiAlternatives(
                subject=assunto,
                body=mensagem_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[locatario.email]
            )
            email.send()
            
            logger.info(f"✅ Recibo enviado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar recibo: {e}")
            return False    
        
