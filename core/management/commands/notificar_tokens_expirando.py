"""
Comando para notificar sobre tokens expirando em breve.
DEV_21.6 - Fase 5

Uso:
    python manage.py notificar_tokens_expirando
    python manage.py notificar_tokens_expirando --dry-run  # Simular sem enviar
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from core.models import Comanda, Pagamento
from core.utils.token_publico import dias_ate_expirar, gerar_url_publica


class Command(BaseCommand):
    help = 'Notifica locatários sobre tokens expirando em 7 dias'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular execução sem enviar emails',
        )
        parser.add_argument(
            '--dias',
            type=int,
            default=7,
            help='Dias de antecedência (padrão: 7)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        dias_antecedencia = options['dias']
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'='*64}\n"
                f"🤖 NOTIFICAÇÃO DE TOKENS EXPIRANDO\n"
                f"{'='*64}\n"
            )
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️ MODO DRY-RUN (simulação)\n"))
        
        # Calcular data limite
        agora = timezone.now()
        limite = agora + timedelta(days=dias_antecedencia)
        
        # Buscar comandas expirando
        comandas = Comanda.objects.filter(
            token_expira_em__lte=limite,
            token_expira_em__gte=agora
        ).select_related('locacao__locatario', 'locacao__imovel')
        
        # Buscar pagamentos expirando
        pagamentos = Pagamento.objects.filter(
            token_expira_em__lte=limite,
            token_expira_em__gte=agora
        ).select_related('comanda__locacao__locatario')
        
        self.stdout.write(f"📊 Encontrados:\n")
        self.stdout.write(f"  • {comandas.count()} comandas expirando\n")
        self.stdout.write(f"  • {pagamentos.count()} recibos expirando\n\n")
        
        # Processar comandas
        enviados_comandas = 0
        erros_comandas = 0
        
        for comanda in comandas:
            try:
                # Verificar email
                if not comanda.locacao or not comanda.locacao.locatario.email:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️ Comanda {comanda.numero_comanda}: Sem email"
                        )
                    )
                    continue
                
                dias_restantes = dias_ate_expirar(comanda)
                url = gerar_url_publica(comanda, 'comanda')
                
                # Preparar email
                email_destino = comanda.locacao.locatario.email
                assunto = f"⚠️ Link da Comanda {comanda.numero_comanda} expira em {dias_restantes} dias"
                mensagem = f"""
Olá {comanda.locacao.locatario.nome_razao_social},

Seu link de acesso à comanda está próximo de expirar!

🔗 Link: {url}
⏰ Expira em: {dias_restantes} dia(s)
📋 Comanda: {comanda.numero_comanda}
🏠 Imóvel: {comanda.locacao.imovel.endereco}, {comanda.locacao.imovel.numero}
📅 Vencimento: {comanda.data_vencimento.strftime('%d/%m/%Y')}
💰 Valor: R$ {comanda.valor_total:,.2f}

⚠️ IMPORTANTE: Após a expiração, será necessário solicitar um novo link.

---
HABITAT PRO
Sistema de Gestão Imobiliária
"""
                
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ [DRY-RUN] Comanda {comanda.numero_comanda} → {email_destino}"
                        )
                    )
                else:
                    # Enviar email
                    send_mail(
                        assunto,
                        mensagem,
                        settings.DEFAULT_FROM_EMAIL,
                        [email_destino],
                        fail_silently=False,
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Email enviado: Comanda {comanda.numero_comanda} → {email_destino}"
                        )
                    )
                
                enviados_comandas += 1
                
            except Exception as e:
                erros_comandas += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Erro comanda {comanda.numero_comanda}: {str(e)}"
                    )
                )
        
        # Processar recibos
        enviados_recibos = 0
        erros_recibos = 0
        
        for pagamento in pagamentos:
            try:
                # Verificar email
                if not pagamento.comanda or not pagamento.comanda.locacao or not pagamento.comanda.locacao.locatario.email:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️ Recibo {pagamento.numero_pagamento}: Sem email"
                        )
                    )
                    continue
                
                dias_restantes = dias_ate_expirar(pagamento)
                url = gerar_url_publica(pagamento, 'recibo')
                
                # Preparar email
                email_destino = pagamento.comanda.locacao.locatario.email
                assunto = f"⚠️ Link do Recibo {pagamento.numero_pagamento} expira em {dias_restantes} dias"
                mensagem = f"""
Olá {pagamento.comanda.locacao.locatario.nome_razao_social},

Seu link de acesso ao recibo está próximo de expirar!

🔗 Link: {url}
⏰ Expira em: {dias_restantes} dia(s)
🧾 Recibo: {pagamento.numero_pagamento}
📅 Data Pagamento: {pagamento.data_pagamento.strftime('%d/%m/%Y')}
💰 Valor Pago: R$ {pagamento.valor_pago:,.2f}

⚠️ IMPORTANTE: Após a expiração, será necessário solicitar um novo link.

---
HABITAT PRO
Sistema de Gestão Imobiliária
"""
                
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ [DRY-RUN] Recibo {pagamento.numero_pagamento} → {email_destino}"
                        )
                    )
                else:
                    # Enviar email
                    send_mail(
                        assunto,
                        mensagem,
                        settings.DEFAULT_FROM_EMAIL,
                        [email_destino],
                        fail_silently=False,
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Email enviado: Recibo {pagamento.numero_pagamento} → {email_destino}"
                        )
                    )
                
                enviados_recibos += 1
                
            except Exception as e:
                erros_recibos += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Erro recibo {pagamento.numero_pagamento}: {str(e)}"
                    )
                )
        
        # Resumo final
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'='*64}\n"
                f"📊 RESUMO:\n"
                f"{'='*64}\n"
                f"Comandas:\n"
                f"  ✅ Enviadas: {enviados_comandas}\n"
                f"  ❌ Erros: {erros_comandas}\n\n"
                f"Recibos:\n"
                f"  ✅ Enviados: {enviados_recibos}\n"
                f"  ❌ Erros: {erros_recibos}\n\n"
                f"TOTAL: {enviados_comandas + enviados_recibos} notificações\n"
                f"{'='*64}\n"
            )
        )
