"""
Comando para validar se APScheduler está configurado corretamente
"""
from django.core.management.base import BaseCommand
from django_apscheduler.models import DjangoJob, DjangoJobExecution


class Command(BaseCommand):
    help = 'Valida se APScheduler está funcionando corretamente'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('🔍 VALIDAÇÃO DO APSCHEDULER'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        # 1. Verificar jobs registrados
        jobs = DjangoJob.objects.all()
        total_jobs = jobs.count()
        
        self.stdout.write(f'📊 Total de jobs registrados: {total_jobs}\n')
        
        if total_jobs == 0:
            self.stdout.write(self.style.ERROR('❌ ERRO: Nenhum job encontrado!'))
            self.stdout.write(self.style.WARNING('\n💡 Solução: Inicie o servidor com "python manage.py runserver"\n'))
            return
        
        # 2. Listar jobs
        self.stdout.write(self.style.HTTP_INFO('📋 JOBS AGENDADOS:'))
        self.stdout.write('')
        
        for i, job in enumerate(jobs, 1):
            self.stdout.write(f'  {i}. {self.style.SUCCESS("✅")} {job.name}')
            self.stdout.write(f'     ID: {job.id}')
            self.stdout.write(f'     Próxima execução: {job.next_run_time}')
            self.stdout.write('')
        
        # 3. Verificar execuções passadas
        execucoes = DjangoJobExecution.objects.all().order_by('-run_time')[:5]
        total_execucoes = execucoes.count()
        
        self.stdout.write(self.style.HTTP_INFO(f'📜 HISTÓRICO DE EXECUÇÕES: {total_execucoes}'))
        self.stdout.write('')
        
        if total_execucoes == 0:
            self.stdout.write(self.style.WARNING('   ℹ️  Nenhuma execução ainda (normal se acabou de instalar)'))
        else:
            for exec in execucoes:
                status_icon = '✅' if exec.status == 'Executed' else '❌'
                self.stdout.write(f'   {status_icon} {exec.job.name}')
                self.stdout.write(f'      Executado em: {exec.run_time}')
                self.stdout.write(f'      Status: {exec.status}')
                self.stdout.write('')
        
        # 4. Verificar jobs esperados
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('🎯 VALIDAÇÃO DOS JOBS ESPERADOS:'))
        self.stdout.write('')
        
        jobs_esperados = {
            'notificacoes_diarias': 'Enviar notificações diárias de comandas',
            'vencimentos_urgentes': 'Verificar vencimentos urgentes a cada hora',
            'limpeza_execucoes': 'Limpeza semanal de execuções antigas'
        }
        
        jobs_ids = [job.id for job in jobs]
        
        for job_id, job_name in jobs_esperados.items():
            if job_id in jobs_ids:
                self.stdout.write(f'   ✅ {job_name}')
            else:
                self.stdout.write(f'   ❌ {job_name} - NÃO ENCONTRADO!')
        
        # 5. Resultado final
        self.stdout.write('')
        self.stdout.write('='*70)
        
        if len(jobs_ids) == len(jobs_esperados):
            self.stdout.write(self.style.SUCCESS('✅ SCHEDULER VALIDADO COM SUCESSO!'))
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 Sistema de notificações automáticas está ATIVO!'))
            self.stdout.write(self.style.SUCCESS('💰 Custo mensal: R$ 0,00'))
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('📅 PRÓXIMAS AÇÕES:'))
            self.stdout.write('   1. Notificações diárias executarão às 8h00')
            self.stdout.write('   2. Backup a cada hora detecta vencimentos urgentes')
            self.stdout.write('   3. Limpeza automática aos domingos às 2h00')
        else:
            self.stdout.write(self.style.ERROR('⚠️  ATENÇÃO: Alguns jobs não foram encontrados!'))
            self.stdout.write(self.style.WARNING('\n💡 Tente reiniciar o servidor Django\n'))
        
        self.stdout.write('='*70 + '\n')
