from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Comanda
from core.sms_utils import SMSNotificador
from core.sms_zenvia import ZenviaNotificador


class Command(BaseCommand):
    help = 'Envia notificações de vencimento e atraso por Email e SMS'
    
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Simulação')
        parser.add_argument('--provider', choices=['twilio', 'zenvia'], default='zenvia', help='Provedor SMS')
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Envio de Notificações'))
        self.stdout.write('=' * 60)
        
        hoje = timezone.now().date()
        
        # Selecionar provedor
        if options['provider'] == 'zenvia':
            sms = ZenviaNotificador()
            provider_name = 'Zenvia'
        else:
            sms = SMSNotificador()
            provider_name = 'Twilio'
        
        self.stdout.write(f'\nData: {hoje.strftime("%d/%m/%Y")}')
        self.stdout.write(f'Provedor SMS: {provider_name}')
        self.stdout.write(f'SMS habilitado: {"Sim" if sms.enabled else "Não (configure credentials)"}')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\nSIMULAÇÃO'))
        
        self.stdout.write('')
        
        enviadas_sms = 0
        erros_sms = 0
        
        # Notificações 7 dias antes
        data_7dias = hoje + timedelta(days=7)
        comandas_7dias = Comanda.objects.filter(
            status='pendente',
            data_vencimento=data_7dias,
            notificacao_enviada_7dias=False
        )
        
        self.stdout.write(f'Notificações 7 dias: {comandas_7dias.count()}')
        for c in comandas_7dias:
            telefone = c.locacao.locatario.telefone
            self.stdout.write(f'  {c.numero_comanda} -> {telefone}', ending='')
            
            if sms.enabled and not options['dry_run']:
                sucesso, resultado = sms.enviar_notificacao_vencimento(c, 7)
                if sucesso:
                    self.stdout.write(' ✓')
                    enviadas_sms += 1
                    c.notificacao_enviada_7dias = True
                    c.save(update_fields=['notificacao_enviada_7dias'])
                else:
                    self.stdout.write(self.style.ERROR(f' ✗ {resultado}'))
                    erros_sms += 1
            else:
                self.stdout.write(' (simulação)')
                enviadas_sms += 1
        
        # Notificações 1 dia antes
        data_1dia = hoje + timedelta(days=1)
        comandas_1dia = Comanda.objects.filter(
            status='pendente',
            data_vencimento=data_1dia,
            notificacao_enviada_1dia=False
        )
        
        self.stdout.write(f'\nNotificações 1 dia: {comandas_1dia.count()}')
        for c in comandas_1dia:
            telefone = c.locacao.locatario.telefone
            self.stdout.write(f'  {c.numero_comanda} -> {telefone}', ending='')
            
            if sms.enabled and not options['dry_run']:
                sucesso, resultado = sms.enviar_notificacao_vencimento(c, 1)
                if sucesso:
                    self.stdout.write(' ✓')
                    enviadas_sms += 1
                    c.notificacao_enviada_1dia = True
                    c.save(update_fields=['notificacao_enviada_1dia'])
                else:
                    self.stdout.write(self.style.ERROR(f' ✗ {resultado}'))
                    erros_sms += 1
            else:
                self.stdout.write(' (simulação)')
                enviadas_sms += 1
        
        # Notificações de atraso
        comandas_atraso = Comanda.objects.filter(
            status='vencida',
            data_vencimento__lt=hoje,
            notificacao_atraso_enviada=False
        )
        
        self.stdout.write(f'\nNotificações atraso: {comandas_atraso.count()}')
        for c in comandas_atraso:
            telefone = c.locacao.locatario.telefone
            dias_atraso = (hoje - c.data_vencimento).days
            self.stdout.write(f'  {c.numero_comanda} ({dias_atraso}d) -> {telefone}', ending='')
            
            if sms.enabled and not options['dry_run']:
                sucesso, resultado = sms.enviar_notificacao_atraso(c, dias_atraso)
                if sucesso:
                    self.stdout.write(' ✓')
                    enviadas_sms += 1
                    c.notificacao_atraso_enviada = True
                    c.save(update_fields=['notificacao_atraso_enviada'])
                else:
                    self.stdout.write(self.style.ERROR(f' ✗ {resultado}'))
                    erros_sms += 1
            else:
                self.stdout.write(' (simulação)')
                enviadas_sms += 1
        
        # Resumo
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(f'SMS enviados: {enviadas_sms}')
        if erros_sms > 0:
            self.stdout.write(self.style.ERROR(f'SMS com erro: {erros_sms}'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('CONCLUÍDO'))
