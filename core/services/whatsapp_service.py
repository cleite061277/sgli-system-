"""
Serviço para geração de mensagens WhatsApp (wa.me)
Segue padrão do sistema existente
HABITAT PRO - Sistema de Gestão Imobiliária
"""
from urllib.parse import quote
from django.conf import settings
from core.models import RenovacaoContrato


class WhatsAppService:
    """Serviço de mensagens WhatsApp para renovações de contrato"""
    
    @staticmethod
    def gerar_mensagem_renovacao_proprietario(renovacao: RenovacaoContrato) -> str:
        """
        Gera mensagem formatada para WhatsApp do proprietário.

        Args:
            renovacao: Objeto RenovacaoContrato

        Returns:
            str: Mensagem em texto plano (não codificada)
        """
        locacao_atual = renovacao.locacao_original
        proprietario = locacao_atual.imovel.locador
        
        # Gerar link da página pública
        base_url = settings.SITE_URL
        link_publico = f"{base_url}/renovacao/proprietario/{renovacao.token_proprietario}/"
        
        # Calcular informações
        dias_vencimento = renovacao.dias_para_vencimento
        aumento = renovacao.aumento_percentual
        
        mensagem = f"""🏠 *HABITAT PRO - Proposta de Renovação*

Olá *{proprietario.nome_razao_social}*,

O contrato do imóvel *{locacao_atual.imovel.endereco_completo}* vence em {dias_vencimento} dias.

📋 *PROPOSTA DE RENOVAÇÃO:*

*Contrato Atual:*
- Locatário: {locacao_atual.locatario.nome_razao_social}
- Vencimento: {locacao_atual.data_fim.strftime('%d/%m/%Y')}
- Valor: R$ {locacao_atual.valor_aluguel:,.2f}

*Nova Proposta:*
- Vigência: {renovacao.nova_data_inicio.strftime('%d/%m/%Y')} a {renovacao.nova_data_fim.strftime('%d/%m/%Y')}
- Valor: R$ {renovacao.novo_valor_aluguel:,.2f} ({'+' if aumento >= 0 else ''}{aumento:.1f}%)
- Duração: {renovacao.nova_duracao_meses} meses
- Garantia: {renovacao.get_novo_tipo_garantia_display()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 *RESPONDA AGORA:*
{link_publico}

⏰ Prazo: 15 dias

Dúvidas? Entre em contato através do sistema.Atenciosamente,
*HABITAT PRO - A&C Imóveis e Sistemas Imobiliários*"""

        return mensagem

    @staticmethod
    def gerar_mensagem_renovacao_locatario(renovacao: RenovacaoContrato) -> str:
        """
        Gera mensagem formatada para WhatsApp do locatário.

        Args:
            renovacao: Objeto RenovacaoContrato

        Returns:
            str: Mensagem em texto plano (não codificada)
        """
        locacao_atual = renovacao.locacao_original
        locatario = locacao_atual.locatario
        
        # Gerar link da página pública
        base_url = settings.SITE_URL
        link_publico = f"{base_url}/renovacao/locatario/{renovacao.token_locatario}/"
        
        # Calcular informações
        aumento = renovacao.aumento_percentual
        diferenca = renovacao.diferenca_aluguel
        
        mensagem = f"""🏠 *HABITAT PRO - Proposta de Renovação*

Olá *{locatario.nome_razao_social}*,

Seu contrato do imóvel *{locacao_atual.imovel.endereco_completo}* foi aprovado para renovação!

📋 *PROPOSTA DE RENOVAÇÃO:*

*Contrato Atual:*
- Vencimento: {locacao_atual.data_fim.strftime('%d/%m/%Y')}
- Valor: R$ {locacao_atual.valor_aluguel:,.2f}

*Nova Proposta:*
- Vigência: {renovacao.nova_data_inicio.strftime('%d/%m/%Y')} a {renovacao.nova_data_fim.strftime('%d/%m/%Y')}
- Valor: R$ {renovacao.novo_valor_aluguel:,.2f} ({'+' if aumento >= 0 else ''}{aumento:.1f}%)
- Diferença: R$ {diferenca:,.2f}/mês
- Garantia: {renovacao.get_novo_tipo_garantia_display()}"""
        
        # Adicionar info de caução se aplicável
        if renovacao.novo_tipo_garantia == 'caucao':
            nova_caucao = renovacao.calcular_nova_caucao()
            mensagem += f"\n• Caução: R$ {nova_caucao:,.2f} ({renovacao.nova_caucao_meses} meses)"
        
        mensagem += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 *ACEITAR OU RECUSAR:*
{link_publico}

⏰ Prazo: 30 dias

Dúvidas? Entre em contato através do sistema.Atenciosamente,
*HABITAT PRO - A&C Imóveis e Sistemas Imobiliários*"""

        return mensagem

    @staticmethod
    def gerar_link_whatsapp(telefone: str, mensagem: str) -> str:
        """
        Gera link completo wa.me com telefone e mensagem.

        Args:
            telefone: Telefone com DDD (ex: 41999999999)
            mensagem: Mensagem em texto plano (será codificada aqui)

        Returns:
            str: URL completa para wa.me
        """
        # Limpar telefone (remover caracteres não numéricos)
        telefone_limpo = ''.join(filter(str.isdigit, telefone))

        # Adicionar código do Brasil se não tiver
        if not telefone_limpo.startswith('55'):
            telefone_limpo = f'55{telefone_limpo}'

        # Gerar link wa.me (mensagem codificada apenas aqui, no destino final)
        return f"https://wa.me/{telefone_limpo}?text={quote(mensagem)}"
