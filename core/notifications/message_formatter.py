"""
Formatador de Mensagens para Email e WhatsApp
Gera mensagens detalhadas com breakdown da comanda
"""
from django.conf import settings
from decimal import Decimal


class MessageFormatter:
    """Formata mensagens para diferentes canais"""
    
    @staticmethod
    def formatar_mensagem_whatsapp(comanda):
        """
        Formata mensagem WhatsApp com detalhamento completo da comanda
        
        Args:
            comanda: Objeto Comanda
            
        Returns:
            str: Mensagem formatada
        """
        locacao = comanda.locacao
        imovel = locacao.imovel
        locatario = locacao.locatario
        
        # Cabeçalho
        msg = "═══════════════════════════════\n"
        msg += "🏠 *COMANDA DE ALUGUEL*\n"
        msg += "═══════════════════════════════\n\n"
        
        # Informações básicas
        msg += f"📍 *Imóvel:* {imovel.endereco_completo or imovel.codigo_imovel}\n"
        msg += f"👤 *Locatário:* {locatario.nome_razao_social}\n"
        msg += f"📅 *Referência:* {comanda.mes_referencia.strftime('%B/%Y')}\n"
        msg += f"📆 *Vencimento:* {comanda.data_vencimento.strftime('%d/%m/%Y')}\n\n"
        
        # Detalhamento
        msg += "───────────────────────────────\n"
        msg += "💰 *DETALHAMENTO*\n"
        msg += "───────────────────────────────\n\n"
        
        # Aluguel base
        msg += f"Aluguel Base{'.' * (20 - len('Aluguel Base'))}R$ {locacao.valor_aluguel:,.2f}\n"
        
        # Itens adicionais da comanda (se houver)
        # Aqui você pode adicionar lógica para itens extras como água, luz, etc.
        # Por exemplo, se tiver campos na comanda:
        # if hasattr(comanda, 'valor_agua') and comanda.valor_agua:
        #     msg += f"Água{'.' * (20 - len('Água'))}R$ {comanda.valor_agua:,.2f}\n"
        
        # Total
        msg += "\n───────────────────────────────\n"
        msg += f"*TOTAL A PAGAR*{'.' * (14)}R$ {comanda.valor_total:,.2f}\n"
        msg += "═══════════════════════════════\n\n"
        
        # Calcular dias para vencimento
        from datetime import date
        dias_restantes = (comanda.data_vencimento - date.today()).days
        
        if dias_restantes > 0:
            msg += f"⏰ *Vence em {dias_restantes} dias!*\n\n"
        elif dias_restantes == 0:
            msg += "⚠️ *VENCE HOJE!*\n\n"
        else:
            msg += f"🚨 *VENCIDO há {abs(dias_restantes)} dias!*\n\n"
        
        msg += "_Mensagem automática - SGLI System_"
        
        return msg
    
    @staticmethod
    def formatar_email_html(comanda):
        """
        Formata email HTML com detalhamento da comanda
        
        Args:
            comanda: Objeto Comanda
            
        Returns:
            str: HTML formatado
        """
        locacao = comanda.locacao
        imovel = locacao.imovel
        locatario = locacao.locatario
        
        # Calcular dias para vencimento
        from datetime import date
        dias_restantes = (comanda.data_vencimento - date.today()).days
        
        if dias_restantes > 0:
            urgencia_cor = "#ffa500"
            urgencia_texto = f"Vence em {dias_restantes} dias"
        elif dias_restantes == 0:
            urgencia_cor = "#ff0000"
            urgencia_texto = "VENCE HOJE"
        else:
            urgencia_cor = "#cc0000"
            urgencia_texto = f"VENCIDO há {abs(dias_restantes)} dias"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #ffffff;
                    padding: 30px;
                    border: 1px solid #ddd;
                }}
                .info-box {{
                    background: #f8f9fa;
                    padding: 15px;
                    margin: 15px 0;
                    border-left: 4px solid #667eea;
                }}
                .detalhamento {{
                    background: #fff;
                    border: 1px solid #ddd;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .item-linha {{
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px dotted #ddd;
                }}
                .total {{
                    font-size: 1.3em;
                    font-weight: bold;
                    color: #667eea;
                    margin-top: 15px;
                    padding-top: 15px;
                    border-top: 2px solid #667eea;
                }}
                .urgencia {{
                    background: {urgencia_cor};
                    color: white;
                    padding: 15px;
                    text-align: center;
                    font-size: 1.2em;
                    font-weight: bold;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    border-radius: 0 0 10px 10px;
                    border: 1px solid #ddd;
                    border-top: none;
                    color: #666;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏠 COMANDA DE ALUGUEL</h1>
                <p>SGLI - Sistema de Gestão de Locação de Imóveis</p>
            </div>
            
            <div class="content">
                <p>Olá, <strong>{locatario.nome_razao_social}</strong>!</p>
                
                <p>Este é um lembrete sobre o pagamento do seu aluguel.</p>
                
                <div class="info-box">
                    <p><strong>📍 Imóvel:</strong> {imovel.endereco_completo or imovel.codigo_imovel}</p>
                    <p><strong>📅 Referência:</strong> {comanda.mes_referencia.strftime('%B/%Y').capitalize()}</p>
                    <p><strong>📆 Vencimento:</strong> {comanda.data_vencimento.strftime('%d/%m/%Y')}</p>
                </div>
                
                <div class="detalhamento">
                    <h3 style="color: #667eea; margin-top: 0;">💰 Detalhamento</h3>
                    
                    <div class="item-linha">
                        <span>Aluguel Base</span>
                        <span><strong>R$ {locacao.valor_aluguel:,.2f}</strong></span>
                    </div>
                    
                    <!-- Aqui podem ser adicionados outros itens -->
                    
                    <div class="total">
                        <div style="display: flex; justify-content: space-between;">
                            <span>TOTAL A PAGAR</span>
                            <span>R$ {comanda.valor_total:,.2f}</span>
                        </div>
                    </div>
                </div>
                
                <div class="urgencia">
                    ⏰ {urgencia_texto.upper()}
                </div>
                
                <p>Por favor, realize o pagamento até a data de vencimento para evitar multas e juros.</p>
                
                <p style="margin-top: 30px;">Atenciosamente,<br><strong>Equipe SGLI</strong></p>
            </div>
            
            <div class="footer">
                <p>Esta é uma mensagem automática. Por favor, não responda.</p>
                <p>Em caso de dúvidas, entre em contato com a administração.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def formatar_email_texto(comanda):
        """
        Formata email em texto puro (fallback)
        
        Args:
            comanda: Objeto Comanda
            
        Returns:
            str: Texto formatado
        """
        locacao = comanda.locacao
        imovel = locacao.imovel
        locatario = locacao.locatario
        
        from datetime import date
        dias_restantes = (comanda.data_vencimento - date.today()).days
        
        texto = "════════════════════════════════════════════\n"
        texto += "COMANDA DE ALUGUEL - SGLI\n"
        texto += "════════════════════════════════════════════\n\n"
        
        texto += f"Olá, {locatario.nome_razao_social}!\n\n"
        texto += "Este é um lembrete sobre o pagamento do seu aluguel.\n\n"
        
        texto += f"Imóvel: {imovel.endereco_completo or imovel.codigo_imovel}\n"
        texto += f"Referência: {comanda.mes_referencia.strftime('%B/%Y').capitalize()}\n"
        texto += f"Vencimento: {comanda.data_vencimento.strftime('%d/%m/%Y')}\n\n"
        
        texto += "────────────────────────────────────────────\n"
        texto += "DETALHAMENTO\n"
        texto += "────────────────────────────────────────────\n\n"
        
        texto += f"Aluguel Base..................R$ {locacao.valor_aluguel:,.2f}\n\n"
        
        texto += "────────────────────────────────────────────\n"
        texto += f"TOTAL A PAGAR.................R$ {comanda.valor_total:,.2f}\n"
        texto += "════════════════════════════════════════════\n\n"
        
        if dias_restantes > 0:
            texto += f"⏰ Vence em {dias_restantes} dias!\n\n"
        elif dias_restantes == 0:
            texto += "⚠️ VENCE HOJE!\n\n"
        else:
            texto += f"🚨 VENCIDO há {abs(dias_restantes)} dias!\n\n"
        
        texto += "Por favor, realize o pagamento até a data de vencimento.\n\n"
        texto += "Atenciosamente,\nEquipe SGLI\n\n"
        texto += "────────────────────────────────────────────\n"
        texto += "Esta é uma mensagem automática.\n"
        
        return texto
