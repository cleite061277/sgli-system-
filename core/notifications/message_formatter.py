# core/notifications/message_formatter.py
"""
Formatador de mensagens para WhatsApp e Email
✅ CORRIGIDO: Adiciona campo 📝 Comentários (observações da comanda)
"""
from django.utils import timezone


def formatar_mensagem_whatsapp_recibo(pagamento, recibo_url: str = None) -> str:
    """
    Formata mensagem de recibo para WhatsApp.
    
    ✅ NOVO: Inclui campo observações da comanda se existir.
    """
    locatario = getattr(pagamento.comanda.locacao, 'locatario', None)
    imovel = getattr(pagamento.comanda.locacao, 'imovel', None)

    nome_locatario = getattr(locatario, 'nome_razao_social', 'Locatário')
    endereco = f"{getattr(imovel, 'endereco', '')}, {getattr(imovel, 'numero', '')}".strip(', ')

    data_pag = pagamento.data_pagamento.strftime('%d/%m/%Y') if pagamento.data_pagamento else timezone.now().strftime('%d/%m/%Y')
    forma = pagamento.get_forma_pagamento_display() if hasattr(pagamento, 'get_forma_pagamento_display') else pagamento.forma_pagamento
    valor = f"R$ {pagamento.valor_pago:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    lines = [
        "📋 RECIBO DE PAGAMENTO",
        "=========================",
        f"🏠 Imóvel: {endereco}",
        f"👤 Locatário: {nome_locatario}",
        f"🧾 Recibo: {pagamento.numero_pagamento}",
        f"📅 Data: {data_pag}",
        f"💳 Forma: {forma}",
        "",
        "-------------------------",
        "💰 VALOR PAGO",
        "-------------------------",
        valor,
    ]

    # ✅ NOVO: Adicionar observações da comanda se existirem
    observacoes = getattr(pagamento.comanda, 'observacoes', None)
    if observacoes and observacoes.strip():
        lines += [
            "",
            "-------------------------",
            "📝 COMENTÁRIOS",
            "-------------------------",
            observacoes.strip(),
        ]

    lines += [
        "",
        "✅ Pagamento confirmado!",
    ]

    if recibo_url:
        lines += ["", f"🔗 Ver recibo completo: {recibo_url}"]

    lines += ["", "—", "HABITAT PRO", "Sistema de Gestão Imobiliária"]
    return "\n".join(lines)


def formatar_mensagem_whatsapp_comanda(comanda) -> str:
    """
    Formata mensagem de comanda (aviso de vencimento) para WhatsApp.
    
    ✅ NOVO: Inclui campo observações da comanda se existir.
    """
    locatario = getattr(comanda.locacao, 'locatario', None)
    imovel = getattr(comanda.locacao, 'imovel', None)

    nome_locatario = getattr(locatario, 'nome_razao_social', 'Locatário')
    endereco = f"{getattr(imovel, 'endereco', '')}, {getattr(imovel, 'numero', '')}".strip(', ')

    data_venc = comanda.data_vencimento.strftime('%d/%m/%Y') if comanda.data_vencimento else 'Não informado'
    valor = f"R$ {comanda.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Status emoji
    status_emoji = {
        'pendente': '⏳',
        'paga': '✅',
        'atrasada': '⚠️',
        'parcial': '🔄'
    }.get(comanda.status.lower(), '📋')

    lines = [
        f"{status_emoji} COMANDA DE PAGAMENTO",
        "=========================",
        f"🏠 Imóvel: {endereco}",
        f"👤 Locatário: {nome_locatario}",
        f"🧾 Comanda: {comanda.numero_comanda}",
        f"📅 Vencimento: {data_venc}",
        "",
        "-------------------------",
        "💰 VALOR TOTAL",
        "-------------------------",
        valor,
    ]

    # Detalhamento de valores (se disponível)
    if hasattr(comanda, 'valor_aluguel') and comanda.valor_aluguel > 0:
        lines += [
            "",
            "📊 Detalhamento:",
            f"  • Aluguel: R$ {comanda.valor_aluguel:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        ]
        if hasattr(comanda, 'valor_condominio') and comanda.valor_condominio > 0:
            lines.append(f"  • Condomínio: R$ {comanda.valor_condominio:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        if hasattr(comanda, 'valor_iptu') and comanda.valor_iptu > 0:
            lines.append(f"  • IPTU: R$ {comanda.valor_iptu:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    # ✅ NOVO: Adicionar observações da comanda se existirem
    observacoes = getattr(comanda, 'observacoes', None)
    if observacoes and observacoes.strip():
        lines += [
            "",
            "-------------------------",
            "📝 COMENTÁRIOS",
            "-------------------------",
            observacoes.strip(),
        ]

    # Mensagem de ação
    if comanda.status.lower() == 'atrasada':
        lines += [
            "",
            "⚠️ ATENÇÃO: Comanda em atraso!",
            "Por favor, regularize o pagamento.",
        ]
    elif comanda.status.lower() == 'pendente':
        lines += [
            "",
            "💡 Lembrete: Vencimento próximo!",
            "Mantenha seus pagamentos em dia.",
        ]

    lines += ["", "—", "HABITAT PRO", "Sistema de Gestão Imobiliária"]
    return "\n".join(lines)


class MessageFormatter:
    """
    Classe para formatação de mensagens.
    
    ✅ Mantém compatibilidade com código existente.
    ✅ Adiciona método para comandas.
    """
    
    @staticmethod
    def formatar_mensagem_whatsapp_recibo(pagamento, recibo_url: str = None) -> str:
        """Formata recibo para WhatsApp."""
        return formatar_mensagem_whatsapp_recibo(pagamento, recibo_url=recibo_url)

    @staticmethod
    def formatar_mensagem_whatsapp_comanda(comanda) -> str:
        """Formata comanda para WhatsApp."""
        return formatar_mensagem_whatsapp_comanda(comanda)

    @staticmethod
    def formatar(pagamento, recibo_url: str = None) -> str:
        """Alias para formatar_mensagem_whatsapp_recibo (retrocompatibilidade)."""
        return formatar_mensagem_whatsapp_recibo(pagamento, recibo_url=recibo_url)
