# core/management/commands/populate_quitado_em.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from core.models import Comanda

class Command(BaseCommand):
    help = "Popula ComandaStatus.quitado_em para comandas já quitadas historicamente."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="Limitar número de comandas processadas.")
        parser.add_argument("--dry-run", action="store_true", help="Mostrar alterações sem persistir.")

    def handle(self, *args, **options):
        qs = Comanda.objects.all().order_by("id")
        if options["limit"]:
            qs = qs[: options["limit"]]
        total = qs.count()
        self.stdout.write(f"Processando {total} comandas...")
        updated = 0
        for com in qs:
            total_pago = com.calcular_total_pago() if hasattr(com, "calcular_total_pago") else (com.valor_pago or Decimal("0.00"))
            valor_total = com.valor_total() if callable(getattr(com, "valor_total", None)) else (com.valor_total or Decimal("0.00"))
            if total_pago >= valor_total:
                ultimo = com.pagamentos.filter(status__iexact="confirmado").order_by("-data_pagamento", "-id").first()
                if ultimo and getattr(ultimo, "data_pagamento", None):
                    quitado_em = timezone.make_aware(
                        timezone.datetime.combine(ultimo.data_pagamento, timezone.datetime.min.time()),
                        timezone.get_current_timezone()
                    )
                else:
                    quitado_em = timezone.now()
                self.stdout.write(f"[OK] Comanda {com.pk} -> quitado_em: {quitado_em} (total_pago={total_pago})")
                if not options["dry_run"]:
                    from core.comanda_status import ComandaStatus
                    cs, created = ComandaStatus.objects.get_or_create(comanda=com)
                    cs.quitado_em = quitado_em
                    cs.save(update_fields=["quitado_em"])
                    com.status = "PAID"
                    com.save(update_fields=["status"])
                    updated += 1
        self.stdout.write(self.style.SUCCESS(f"Concluído. Atualizadas: {updated} comandas."))
