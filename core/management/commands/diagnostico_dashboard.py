from django.core.management.base import BaseCommand
from django.db.models import Sum
from datetime import datetime

class Command(BaseCommand):
    help = "Diagnostico do dashboard financeiro em producao"

    def handle(self, *args, **kwargs):
        from core.models import Pagamento, Comanda
        from core.models_rescisao import ComandaRescisao

        data_inicio = datetime(2026, 2, 1).date()
        data_fim = datetime(2026, 2, 28).date()

        total_pags = Pagamento.objects.filter(
            data_pagamento__gte=data_inicio,
            data_pagamento__lte=data_fim,
            status="confirmado"
        ).count()

        aluguel = Pagamento.objects.filter(
            data_pagamento__gte=data_inicio,
            data_pagamento__lte=data_fim,
            status="confirmado",
            comanda_id__isnull=False
        ).aggregate(t=Sum("valor_pago"))["t"] or 0

        rescisao = Pagamento.objects.filter(
            data_pagamento__gte=data_inicio,
            data_pagamento__lte=data_fim,
            status="confirmado",
            content_type_id__isnull=False
        ).aggregate(t=Sum("valor_pago"))["t"] or 0

        cmd_count = Comanda.objects.filter(
            mes_referencia__gte=data_inicio,
            mes_referencia__lte=data_fim,
            is_active=True
        ).count()

        cmd_rescisao_count = ComandaRescisao.objects.filter(
            data_vencimento__gte=data_inicio,
            data_vencimento__lte=data_fim,
            is_active=True
        ).count()

        prevista_aluguel = Comanda.objects.filter(
            mes_referencia__gte=data_inicio,
            mes_referencia__lte=data_fim,
            is_active=True
        ).aggregate(t=Sum("_valor_aluguel_historico"))["t"] or 0

        prevista_rescisao = ComandaRescisao.objects.filter(
            data_vencimento__gte=data_inicio,
            data_vencimento__lte=data_fim,
            is_active=True
        ).aggregate(t=Sum("valor"))["t"] or 0

        self.stdout.write("=== DIAGNOSTICO DASHBOARD FEV/2026 ===")
        self.stdout.write(f"Pagamentos confirmados: {total_pags}")
        self.stdout.write(f"Receita realizada aluguel: R$ {aluguel}")
        self.stdout.write(f"Receita realizada rescisao: R$ {rescisao}")
        self.stdout.write(f"Comandas aluguel no periodo: {cmd_count}")
        self.stdout.write(f"Comandas rescisao no periodo: {cmd_rescisao_count}")
        self.stdout.write(f"Receita prevista aluguel: R$ {prevista_aluguel}")
        self.stdout.write(f"Receita prevista rescisao: R$ {prevista_rescisao}")
        self.stdout.write(f"TOTAL PREVISTO: R$ {float(prevista_aluguel)+float(prevista_rescisao)}")
        self.stdout.write(f"TOTAL REALIZADO: R$ {float(aluguel)+float(rescisao)}")
