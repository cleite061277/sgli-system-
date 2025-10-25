"""
Comando: python manage.py validar_notificacoes
Valida configuração do sistema de notificações
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from core.notifications import EmailSender, WhatsAppSender
from core.models import Comanda, Locatario
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Valida configuração do sistema de notificações'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('VALIDAÇÃO DO SISTEMA DE NOTIFICAÇÕES'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        
        problemas = []
        avisos = []
        
        # 1. Verificar Django-Q
        self.stdout.write('📦 [1/8] Verificando Django-Q...')
        try:
            from django_q.models import Schedule
            schedules = Schedule.objects.filter(func='core.tasks.enviar_lembretes_vencimento')
            
            if schedules.exists():
                self.stdout.write(self.style.SUCCESS('   ✅ Agendamento configurado'))
                schedule = schedules.first()
                self.stdout.write(f"      Próxima execução: {schedule.next_run}")
            else:
                avisos.append('Agendamento não configurado')
                self.stdout.write(self.style.WARNING('   ⚠️  Agendamento não configurado'))
                self.stdout.write('      Execute: python manage.py configurar_agendamento')
        except Exception as e:
            problemas.append(f'Django-Q: {str(e)}')
            self.stdout.write(self.style.ERROR(f'   ❌ Erro: {str(e)}'))
        
        self.stdout.write('')
        
        # 2. Verificar configurações no .env
        self.stdout.write('⚙️  [2/8] Verificando configurações (.env)...')
        
        if settings.NOTIFICACOES_ATIVAS:
            self.stdout.write(self.style.SUCCESS('   ✅ Notificações ATIVAS'))
        else:
            avisos.append('Notificações desativadas')
            self.stdout.write(self.style.WARNING('   ⚠️  Notificações DESATIVADAS'))
            self.stdout.write('      Altere NOTIFICACOES_ATIVAS=True no .env')
        
        self.stdout.write(f"   Dias antecedência: {settings.DIAS_ANTECEDENCIA_LEMBRETE}")
        self.stdout.write(f"   Horário de envio: {settings.HORARIO_ENVIO}")
        self.stdout.write(f"   Email ativo: {settings.ENVIAR_EMAIL}")
        self.stdout.write(f"   WhatsApp ativo: {settings.ENVIAR_WHATSAPP}")
        
        self.stdout.write('')
        
        # 3. Verificar Email
        self.stdout.write('📧 [3/8] Verificando configuração de Email...')
        
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
            self.stdout.write(self.style.SUCCESS('   ✅ Credenciais de email configuradas'))
            self.stdout.write(f"      Email: {settings.EMAIL_HOST_USER}")
            self.stdout.write(f"      Servidor: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        else:
            avisos.append('Email não configurado')
            self.stdout.write(self.style.WARNING('   ⚠️  Email não configurado'))
            self.stdout.write('      Configure EMAIL_HOST_USER e EMAIL_HOST_PASSWORD no .env')
        
        self.stdout.write('')
        
        # 4. Verificar Twilio
        self.stdout.write('📱 [4/8] Verificando configuração Twilio...')
        
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.stdout.write(self.style.SUCCESS('   ✅ Credenciais Twilio configuradas'))
            self.stdout.write(f"      Account SID: {settings.TWILIO_ACCOUNT_SID[:10]}...")
            self.stdout.write(f"      WhatsApp de: {settings.TWILIO_WHATSAPP_FROM}")
        else:
            avisos.append('Twilio não configurado')
            self.stdout.write(self.style.WARNING('   ⚠️  Twilio não configurado'))
            self.stdout.write('      Configure TWILIO_ACCOUNT_SID e TWILIO_AUTH_TOKEN no .env')
        
        self.stdout.write('')
        
        # 5. Verificar banco de dados
        self.stdout.write('🗄️  [5/8] Verificando banco de dados...')
        
        try:
            total_locatarios = Locatario.objects.count()
            self.stdout.write(self.style.SUCCESS(f'   ✅ {total_locatarios} locatários cadastrados'))
            
            # Verificar locatários com email
            com_email = Locatario.objects.exclude(email__isnull=True).exclude(email='').count()
            self.stdout.write(f"      Com email: {com_email}")
            
            # Verificar locatários com telefone
            com_telefone = Locatario.objects.exclude(telefone__isnull=True).exclude(telefone='').count()
            self.stdout.write(f"      Com telefone: {com_telefone}")
            
            if com_email == 0:
                avisos.append('Nenhum locatário tem email cadastrado')
            if com_telefone == 0:
                avisos.append('Nenhum locatário tem telefone cadastrado')
                
        except Exception as e:
            problemas.append(f'Banco de dados: {str(e)}')
            self.stdout.write(self.style.ERROR(f'   ❌ Erro: {str(e)}'))
        
        self.stdout.write('')
        
        # 6. Verificar comandas
        self.stdout.write('📋 [6/8] Verificando comandas...')
        
        try:
            total_comandas = Comanda.objects.count()
            pendentes = Comanda.objects.filter(status='PENDENTE').count()
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ {total_comandas} comandas no sistema'))
            self.stdout.write(f"      Pendentes: {pendentes}")
            
            # Comandas que vencem nos próximos X dias
            dias = settings.DIAS_ANTECEDENCIA_LEMBRETE
            data_alvo = date.today() + timedelta(days=dias)
            futuras = Comanda.objects.filter(
                data_vencimento=data_alvo,
                status='PENDENTE'
            ).count()
            
            self.stdout.write(f"      Vencem em {dias} dias: {futuras}")
            
            if futuras == 0:
                avisos.append(f'Nenhuma comanda vence em {dias} dias')
                
        except Exception as e:
            problemas.append(f'Comandas: {str(e)}')
            self.stdout.write(self.style.ERROR(f'   ❌ Erro: {str(e)}'))
        
        self.stdout.write('')
        
        # 7. Verificar sistema principal
        self.stdout.write('🏠 [7/8] Verificando sistema principal...')
        
        from django.core.management import call_command
        from io import StringIO
        
        try:
            out = StringIO()
            call_command('check', stdout=out, stderr=out)
            self.stdout.write(self.style.SUCCESS('   ✅ Sistema Django OK'))
        except Exception as e:
            problemas.append(f'Sistema Django: {str(e)}')
            self.stdout.write(self.style.ERROR(f'   ❌ Erro: {str(e)}'))
        
        self.stdout.write('')
        
        # 8. Teste de importações
        self.stdout.write('📦 [8/8] Verificando módulos...')
        
        try:
            from core.tasks import enviar_lembretes_vencimento, enviar_lembrete_manual
            from core.notifications import EmailSender, WhatsAppSender, MessageFormatter
            from core.notifications.models import NotificacaoLog
            
            self.stdout.write(self.style.SUCCESS('   ✅ Todos os módulos importados com sucesso'))
        except ImportError as e:
            problemas.append(f'Importação: {str(e)}')
            self.stdout.write(self.style.ERROR(f'   ❌ Erro de importação: {str(e)}'))
        
        self.stdout.write('')
        
        # Resumo
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('RESUMO DA VALIDAÇÃO'))
        self.stdout.write('=' * 60)
        self.stdout.write('')
        
        if not problemas and not avisos:
            self.stdout.write(self.style.SUCCESS('🎉 SISTEMA 100% CONFIGURADO E PRONTO!'))
            self.stdout.write('')
            self.stdout.write('✅ Todas as verificações passaram')
            self.stdout.write('✅ Sistema pronto para uso')
            self.stdout.write('')
            self.stdout.write('📋 Próximos passos:')
            self.stdout.write('   1. Configurar credenciais (se ainda não fez)')
            self.stdout.write('   2. Ativar notificações: NOTIFICACOES_ATIVAS=True')
            self.stdout.write('   3. Iniciar worker: ./iniciar_worker.sh')
            
        elif problemas:
            self.stdout.write(self.style.ERROR('❌ PROBLEMAS ENCONTRADOS:'))
            self.stdout.write('')
            for p in problemas:
                self.stdout.write(self.style.ERROR(f'   • {p}'))
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('⚠️  Corrija os problemas antes de usar'))
            
        elif avisos:
            self.stdout.write(self.style.WARNING('⚠️  AVISOS:'))
            self.stdout.write('')
            for a in avisos:
                self.stdout.write(self.style.WARNING(f'   • {a}'))
            self.stdout.write('')
            self.stdout.write('Sistema funcional, mas requer configuração adicional')
        
        self.stdout.write('')
        self.stdout.write('=' * 60)
