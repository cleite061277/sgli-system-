# core/models/comanda_status.py
from django.db import models

class ComandaStatus(models.Model):
    """
    Armazena dados complementares da comanda sem modificar diretamente o modelo principal.
    Guarda a data de quitação para "congelar" dias de atraso.
    """
    comanda = models.OneToOneField("core.Comanda", on_delete=models.CASCADE, related_name="status_info")
    quitado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Comanda Status"
        verbose_name_plural = "Comandas Status"

    def __str__(self):
        return f"ComandaStatus(comanda={self.comanda_id}, quitado_em={self.quitado_em})"
