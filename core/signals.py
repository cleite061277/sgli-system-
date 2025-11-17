# core/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import Pagamento, Comanda

@receiver(post_save, sender=Pagamento)
def pagamento_saved(sender, instance, created, **kwargs):
    if not getattr(instance, "comanda_id", None):
        return
    try:
        with transaction.atomic():
            comanda = Comanda.objects.select_for_update().get(pk=instance.comanda_id)
            comanda.atualizar_status_e_quitacao()
    except Comanda.DoesNotExist:
        return

@receiver(post_delete, sender=Pagamento)
def pagamento_deleted(sender, instance, **kwargs):
    if not getattr(instance, "comanda_id", None):
        return
    try:
        with transaction.atomic():
            comanda = Comanda.objects.select_for_update().get(pk=instance.comanda_id)
            comanda.atualizar_status_e_quitacao()
    except Comanda.DoesNotExist:
        return
