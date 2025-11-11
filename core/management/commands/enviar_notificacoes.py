"""
Management command para enviar notificações de cobranças
Pode ser executado manualmente ou via Celery Beat
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Comanda, LogNotificacao
from core.services.email_service import EmailService
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Envia notificações de cobrança automáticas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula execução sem enviar emails',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        hoje = date.today()
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS(f'🚀 INICIANDO ENVIO DE NOTIFICAÇÕES - {hoje}'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODO DRY-RUN (não enviará emails)\n'))
        
        stats = {
            '10D': 0, '7D': 0, '1D': 0, 'VEN': 0,
            'ATR1': 0, 'ATR7': 0, 'ATR14': 0, 'ATR21': 0,
            'total': 0, 'erros': 0
        }
        
        # 1. LEMBRETES ANTES DO VENCIMENTO
        self.stdout.write(self.style.HTTP_INFO('\n📋 LEMBRETES ANTES DO VENCIMENTO'))
        
        # 10 dias antes
        comandas_10d = Comanda.objects.filter(
            data_vencimento=hoje + timedelta(days=10),
            status__in=['PENDING', 'OVERDUE'],
            notificacao_enviada_10dias=False,
            is_active=True
        )
        stats['10D'] = self._processar_lote(comandas_10d, '10D', 'notificacao_enviada_10dias', dry_run)
        
        # 7 dias antes
        comandas_7d = Comanda.objects.filter(
            data_vencimento=hoje + timedelta(days=7),
            status__in=['PENDING', 'OVERDUE'],
            notificacao_enviada_7dias=False,
            is_active=True
        )
        stats['7D'] = self._processar_lote(comandas_7d, '7D', 'notificacao_enviada_7dias', dry_run)
        
        # 1 dia antes
        comandas_1d = Comanda.objects.filter(
            data_vencimento=hoje + timedelta(days=1),
            status__in=['PENDING', 'OVERDUE'],
            notificacao_enviada_1dia=False,
            is_active=True
        )
        stats['1D'] = self._processar_lote(comandas_1d, '1D', 'notificacao_enviada_1dia', dry_run)
        
        # Dia do vencimento
        comandas_ven = Comanda.objects.filter(
            data_vencimento=hoje,
            status__in=['PENDING', 'OVERDUE'],
            notificacao_enviada_vencimento=False,
            is_active=True
        )
        stats['VEN'] = self._processar_lote(comandas_ven, 'VEN', 'notificacao_enviada_vencimento', dry_run)
        
        # 2. COBRANÇAS DE ATRASO
        self.stdout.write(self.style.HTTP_INFO('\n⚠️  COBRANÇAS DE ATRASO'))
        
        # 1 dia de atraso
        comandas_atr1 = Comanda.objects.filter(
            data_vencimento=hoje - timedelta(days=1),
            status__in=['PENDING', 'OVERDUE'],
            notificacao_atraso_enviada=False,
            is_active=True
        )
        stats['ATR1'] = self._processar_lote(comandas_atr1, 'ATR1', 'notificacao_atraso_enviada', dry_run)
        
        # Atrasos de 7, 14, 21 dias (sempre envia, sem flag)
        for dias in [7, 14, 21]:
            comandas_atr = Comanda.objects.filter(
                data_vencimento=hoje - timedelta(days=dias),
                status__in=['PENDING', 'OVERDUE'],
                is_active=True
            )
            tipo = f'ATR{dias}'
            stats[tipo] = self._processar_lote(comandas_atr, tipo, None, dry_run)
        
        # 3. RESUMO
        stats['total'] = sum(stats.values())
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS('📊 RESUMO DA EXECUÇÃO'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}'))
        self.stdout.write(f'🔔 Lembretes 10 dias: {stats["10D"]}')
        self.stdout.write(f'🔔 Lembretes 7 dias: {stats["7D"]}')
        self.stdout.write(f'🔔 Lembretes 1 dia: {stats["1D"]}')
        self.stdout.write(f'🔔 Dia vencimento: {stats["VEN"]}')
        self.stdout.write(f'⚠️  Atraso 1 dia: {stats["ATR1"]}')
        self.stdout.write(f'⚠️  Atraso 7 dias: {stats["ATR7"]}')
        self.stdout.write(f'⚠️  Atraso 14 dias: {stats["ATR14"]}')
        self.stdout.write(f'⚠️  Atraso 21 dias: {stats["ATR21"]}')
        self.stdout.write(self.style.SUCCESS(f'\n✅ TOTAL ENVIADO: {stats["total"]}'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))
    
    def _processar_lote(self, queryset, tipo_notificacao, flag_campo, dry_run):
        """Processa um lote de comandas"""
        count = queryset.count()
        enviados = 0
        
        if count == 0:
            return 0
        
        self.stdout.write(f'\n  📨 Processando {count} comanda(s) - {tipo_notificacao}')
        
        for comanda in queryset:
            if dry_run:
                self.stdout.write(f'    [DRY-RUN] {comanda.numero_comanda} → {comanda.locacao.locatario.email}')
                enviados += 1
            else:
                sucesso = EmailService.enviar_notificacao(comanda, tipo_notificacao)
                if sucesso:
                    if flag_campo:
                        setattr(comanda, flag_campo, True)
                        comanda.save(update_fields=[flag_campo, 'updated_at'])
                    enviados += 1
                    self.stdout.write(self.style.SUCCESS(f'    ✅ {comanda.numero_comanda}'))
                else:
                    self.stdout.write(self.style.ERROR(f'    ❌ {comanda.numero_comanda}'))
        
        return enviados
