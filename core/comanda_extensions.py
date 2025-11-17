# core/comanda_extensions.py
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce

def calcular_total_pago(self):
    total = self.pagamentos.filter(status__iexact="confirmado").aggregate(
        total=Coalesce(Sum("valor_pago"), Decimal("0.00"))
    )["total"]
    return Decimal(total or 0)

@property
def saldo(self):
    return calcular_total_pago(self) - (self.valor_total() if callable(getattr(self, "valor_total", None)) else (self.valor_total or Decimal("0.00")))

@property
def valor_pendente(self):
    valor_total = self.valor_total() if callable(getattr(self, "valor_total", None)) else (self.valor_total or Decimal("0.00"))
    return valor_total - calcular_total_pago(self)

def atualizar_status_e_quitacao(self):
    from core.comanda_status import ComandaStatus
    with transaction.atomic():
        comanda = self.__class__.objects.select_for_update().get(pk=self.pk)
        total_pago = calcular_total_pago(comanda)
        valor_total = comanda.valor_total() if callable(getattr(comanda, "valor_total", None)) else (comanda.valor_total or Decimal("0.00"))

        if total_pago >= valor_total:
            cs, created = ComandaStatus.objects.get_or_create(comanda=comanda)
            if not cs.quitado_em:
                ultimo = comanda.pagamentos.filter(status__iexact="confirmado").order_by("-data_pagamento", "-id").first()
                if ultimo and getattr(ultimo, "data_pagamento", None):
                    dt = getattr(ultimo, "data_pagamento")
                    try:
                        cs.quitado_em = timezone.make_aware(
                            timezone.datetime.combine(dt, timezone.datetime.min.time()),
                            timezone.get_current_timezone(),
                        )
                    except Exception:
                        cs.quitado_em = timezone.now()
                else:
                    cs.quitado_em = timezone.now()
                cs.save(update_fields=["quitado_em"])
            comanda.status = "PAID"
        else:
            try:
                cs = comanda.status_info
                if cs and cs.quitado_em:
                    cs.quitado_em = None
                    cs.save(update_fields=["quitado_em"])
            except Exception:
                pass
            comanda.status = "PENDING"
        comanda.save(update_fields=["status"])

def dias_atraso(self):
    if not getattr(self, "data_vencimento", None):
        return 0
    venc = self.data_vencimento
    try:
        cs = getattr(self, "status_info", None)
        if cs and cs.quitado_em:
            fim = cs.quitado_em.date()
        else:
            fim = timezone.localdate()
        dias = (fim - venc).days
        return dias if dias > 0 else 0
    except Exception:
        return 0

def bind():
    try:
        from .models import Comanda  # noqa
        Comanda.calcular_total_pago = calcular_total_pago
        Comanda.saldo = property(saldo)
        Comanda.valor_pendente = property(valor_pendente)
        Comanda.atualizar_status_e_quitacao = atualizar_status_e_quitacao
        Comanda.dias_atraso = dias_atraso
    except Exception:
        pass
