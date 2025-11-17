# Substitua/mescle o método save() da classe Comanda por este trecho
# (coloque dentro da classe Comanda, com a indentação correta)

from django.db import transaction, IntegrityError
from django.utils import timezone

def save(self, *args, **kwargs):
    """
    Save override para Comanda: gera numero_comanda no formato YYYYMM-XXXX.
    - Usa retry atômico (UNIQUE + transaction) para evitar colisões.
    - NÃO usa SequenceCounter (apenas Pagamento usa SequenceCounter).
    """
    # Se o modelo não tiver numero_comanda, delega ao save padrão
    if not hasattr(self, 'numero_comanda'):
        return super(type(self), self).save(*args, **kwargs)

    # Se já existe numero_comanda (edição), salva normalmente
    if self.numero_comanda:
        return super().save(*args, **kwargs)

    # Mes_referencia é DateField -> extrair ano e mês com segurança
    if hasattr(self, 'mes_referencia') and getattr(self.mes_referencia, 'month', None):
        when_year = int(self.mes_referencia.year)
        when_month = int(self.mes_referencia.month)
    else:
        # fallback (se por algum motivo mes_referencia for number)
        when_year = int(self.ano_referencia)
        when_month = int(self.mes_referencia)

    prefix = f"{when_year}{when_month:02d}"  # ex: '202511'

    MAX_ATTEMPTS = 8
    last_exc = None

    for attempt in range(MAX_ATTEMPTS):
        try:
            with transaction.atomic():
                last = (Comanda.objects
                        .filter(numero_comanda__startswith=prefix)
                        .order_by('-numero_comanda')
                        .first())

                if last and getattr(last, 'numero_comanda', None):
                    try:
                        last_seq = int(last.numero_comanda.split('-')[-1])
                        new_seq = last_seq + 1
                    except (IndexError, ValueError):
                        new_seq = 1
                else:
                    new_seq = 1

                self.numero_comanda = f"{prefix}-{new_seq:04d}"

                # Salva; IntegrityError será levantado em caso de colisão UNIQUE
                super().save(*args, **kwargs)

            # sucesso
            return

        except IntegrityError as exc:
            last_exc = exc
            # limpar para tentar novamente
            self.numero_comanda = None
            continue

    # esgotou tentativas
    raise IntegrityError(f"Não foi possível gerar numero_comanda único após {MAX_ATTEMPTS} tentativas") from last_exc