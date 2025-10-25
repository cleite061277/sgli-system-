"""
Comando: python manage.py configurar_agendamento
Configura o agendamento automático no Django-Q
"""
from django.core.management.base import BaseCommand
from django_q.models import Schedule
from django.conf import settings


class Command(BaseCommand):
    help = 'Configura agendamento automático de lembretes'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('CONFIGURANDO AGENDAMENTO AUTOMÁTICO'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        
        # Verificar se já existe agendamento
        agendamento_existente = Schedule.objects.filter(
            func='core.tasks.enviar_lembretes_vencimento',
            name='Envio Diário de Lembretes'
        ).first()
        
        if agendamento_existente:
            self.stdout.write(self.style.WARNING('⚠️  Agendamento já existe!'))
            self.stdout.write('')
            self.stdout.write(f"   Nome: {agendamento_existente.name}")
            self.stdout.write(f"   Função: {agendamento_existente.func}")
            self.stdout.write(f"   Horário: {agendamento_existente.schedule_type}")
            self.stdout.write(f"   Próxima execução: {agendamento_existente.next_run}")
            self.stdout.write('')
            
            resposta = input('Deseja reconfigurar? (s/n): ')
            if resposta.lower() != 's':
                self.stdout.write(self.style.WARNING('Operação cancelada.'))
                return
            
            # Deletar agendamento existente
            agendamento_existente.delete()
            self.stdout.write(self.style.SUCCESS('✅ Agendamento anterior removido'))
            self.stdout.write('')
        
        # Obter horário configurado
        horario = settings.HORARIO_ENVIO  # Formato: "09:00"
        hora, minuto = horario.split(':')
        
        # Criar novo agendamento
        schedule = Schedule.objects.create(
            func='core.tasks.enviar_lembretes_vencimento',
            name='Envio Diário de Lembretes',
            schedule_type=Schedule.DAILY,
            minutes=int(minuto),
            repeats=-1,  # Infinito
        )
        
        # Configurar horário específico (cron)
        schedule.cron = f"{minuto} {hora} * * *"
        schedule.save()
        
        self.stdout.write(self.style.SUCCESS('✅ AGENDAMENTO CONFIGURADO!'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('📋 Detalhes:'))
        self.stdout.write(f"   Nome: {schedule.name}")
        self.stdout.write(f"   Função: {schedule.func}")
        self.stdout.write(f"   Horário: {horario} (todos os dias)")
        self.stdout.write(f"   Cron: {schedule.cron}")
        self.stdout.write(f"   Próxima execução: {schedule.next_run}")
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('⚠️  IMPORTANTE:'))
        self.stdout.write(self.style.WARNING('   Para o agendamento funcionar, o worker do Django-Q'))
        self.stdout.write(self.style.WARNING('   deve estar rodando:'))
        self.stdout.write('')
        self.stdout.write('   python manage.py qcluster')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
