# Substitua/mescle a implementação do SequenceCounter.get_next por esta versão robusta.

from django.db import transaction, IntegrityError
from django.db.models import F

class SequenceCounter(models.Model):
    name = models.CharField(max_length=100, unique=True)
    last_value = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_sequencecounter"

    @classmethod
    def get_next(cls, prefix: str, max_attempts: int = 8) -> int:
        """
        Retorna o próximo valor para a sequência 'prefix' de forma atômica.
        - Usa select_for_update() + F() para garantir incremento atômico.
        - Em caso de colisão/IntegrityError, tenta novamente até max_attempts.
        - Retorna inteiro do próximo valor.
        """
        last_exc = None
        for attempt in range(max_attempts):
            try:
                with transaction.atomic():
                    obj, created = cls.objects.select_for_update().get_or_create(
                        name=prefix, defaults={'last_value': 0}
                    )
                    # incremento atômico usando F()
                    obj.last_value = F('last_value') + 1
                    obj.save(update_fields=['last_value'])
                    # refresh para obter o valor atualizado como int
                    obj.refresh_from_db(fields=['last_value'])
                    return int(obj.last_value)
            except IntegrityError as exc:
                # colisão ou outra falha transacional — tentar de novo
                last_exc = exc
                continue

        # se esgotou tentativas, raise para investigação (log upstream)
        raise IntegrityError(f"get_next failed after {max_attempts} attempts") from last_exc