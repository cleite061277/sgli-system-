from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Recalcula valor_pago + corrige pagamentos mal classificados'

    def handle(self, *args, **kwargs):
        from core.models import Comanda, Pagamento
        from core.models_rescisao import ComandaRescisao

        ct_rescisao = ContentType.objects.get_for_model(ComandaRescisao)
        ct_comanda = ContentType.objects.get_for_model(Comanda)

        # ══════════════════════════════════════════════════════
        # FASE 1: Corrigir pagamentos mal classificados
        # Pagamento com comanda_id (aluguel) E content_type_id
        # preenchidos simultaneamente → remover content_type
        # ══════════════════════════════════════════════════════
        self.stdout.write('=== FASE 1: Pagamentos mal classificados ===')
        mal_classificados = Pagamento.objects.filter(
            comanda_id__isnull=False,
            content_type_id__isnull=False
        )
        count_fix = 0
        for pag in mal_classificados:
            self.stdout.write(
                f'  CORRIGINDO {pag.numero_pagamento}: '
                f'comanda={pag.comanda_id} content_type={pag.content_type_id} '
                f'→ removendo content_type/object_id'
            )
            pag.content_type = None
            pag.object_id = None
            pag.save(update_fields=['content_type', 'object_id'])
            count_fix += 1
        self.stdout.write(f'Fase 1: {count_fix} pagamento(s) corrigido(s)')

        # ══════════════════════════════════════════════════════
        # FASE 2: Recalcular valor_pago nas Comandas de aluguel
        # ══════════════════════════════════════════════════════
        self.stdout.write('=== FASE 2: Comandas de Aluguel ===')
        atualizadas = 0
        for c in Comanda.objects.all():
            total = c.pagamentos.filter(
                status='confirmado'
            ).aggregate(t=Sum('valor_pago'))['t'] or 0
            if c.valor_pago != total:
                c.valor_pago = total
                c.save(update_fields=['valor_pago'])
                atualizadas += 1
                self.stdout.write(f'  {c.numero_comanda}: valor_pago={total}')
        self.stdout.write(f'Fase 2: {atualizadas} comanda(s) atualizada(s)')

        # ══════════════════════════════════════════════════════
        # FASE 3: Recalcular valor_pago nas Comandas de Rescisão
        # ══════════════════════════════════════════════════════
        self.stdout.write('=== FASE 3: Comandas de Rescisão ===')
        atualizadas = 0
        for cr in ComandaRescisao.objects.all():
            total = Pagamento.objects.filter(
                content_type=ct_rescisao,
                object_id=cr.pk,
                status='confirmado'
            ).aggregate(t=Sum('valor_pago'))['t'] or 0
            if cr.valor_pago != total:
                cr.valor_pago = total
                cr.save(update_fields=['valor_pago'])
                atualizadas += 1
                self.stdout.write(f'  {str(cr.id)[:8]}: valor_pago={total}')
        self.stdout.write(f'Fase 3: {atualizadas} comanda(s) atualizada(s)')

        # ══════════════════════════════════════════════════════
        # FASE 4: Recalcular status baseado no valor_pago
        # ══════════════════════════════════════════════════════
        self.stdout.write('=== FASE 4: Recalcular status Rescisão ===')
        atualizadas = 0
        for cr in ComandaRescisao.objects.all():
            if cr.valor_pago >= cr.valor and cr.valor > 0:
                novo_status = 'PAGO'
            elif cr.valor_pago > 0:
                novo_status = 'PENDENTE'
            else:
                novo_status = 'PENDENTE'
            if cr.status != novo_status:
                cr.status = novo_status
                cr.save(update_fields=['status'])
                atualizadas += 1
                self.stdout.write(f'  {str(cr.id)[:8]}: status={novo_status}')
        self.stdout.write(f'Fase 4: {atualizadas} status atualizado(s)')

        self.stdout.write('✅ RECALCULO CONCLUÍDO')
