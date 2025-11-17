# core/notifications/message_formatter.py
from django.utils import timezone

def formatar_mensagem_whatsapp_recibo(pagamento, recibo_url: str = None) -> str:
    locatario = getattr(pagamento.comanda.locacao, 'locatario', None)
    imovel = getattr(pagamento.comanda.locacao, 'imovel', None)

    nome_locatario = getattr(locatario, 'nome_razao_social', 'Locatário')
    endereco = f"{getattr(imovel, 'endereco', '')}, {getattr(imovel, 'numero', '')}".strip(', ')

    data_pag = pagamento.data_pagamento.strftime('%d/%m/%Y') if pagamento.data_pagamento else timezone.now().strftime('%d/%m/%Y')
    forma = pagamento.get_forma_pagamento_display() if hasattr(pagamento, 'get_forma_pagamento_display') else pagamento.forma_pagamento
    valor = f"R$ {pagamento.valor_pago:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    lines = [
        "RECIBO DE PAGAMENTO",
        "=========================",
        f"🏠 Imóvel: {endereco}",
        f"👤 Locatário: {nome_locatario}",
        f"🧾 Recibo: {pagamento.numero_pagamento}",
        f"📅 Data: {data_pag}",
        f"💳 Forma: {forma}",
        "",
        "-------------------------",
        "VALOR PAGO",
        "-------------------------",
        valor,
        "",
        "Pagamento confirmado! ✅",
    ]

    if recibo_url:
        lines += ["", f"Ver recibo completo: {recibo_url}"]

    lines += ["", "—", "HABITAT PRO", "Sistema de Gestão Imobiliária"]
    return "\n".join(lines)


class MessageFormatter:
    @staticmethod
    def formatar_mensagem_whatsapp_recibo(pagamento, recibo_url: str = None) -> str:
        return formatar_mensagem_whatsapp_recibo(pagamento, recibo_url=recibo_url)

    @staticmethod
    def formatar(pagamento, recibo_url: str = None) -> str:
        return formatar_mensagem_whatsapp_recibo(pagamento, recibo_url=recibo_url)
