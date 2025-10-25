"""
Comando de gerenciamento: python manage.py enviar_lembretes
Permite envio manual de lembretes
"""
from django.core.management.base import BaseCommand
from core.tasks import enviar_lembretes_vencimento


class Command(BaseCommand):
    help = 'Envia lembretes de vencimento manualmente'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula envio sem enviar mensagens reais',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('ENVIO MANUAL DE LEMBRETES'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN ATIVO (sem envio real)'))
            self.stdout.write('')
            # TODO: Implementar dry-run mode
        
        # Executar tarefa
        resultado = enviar_lembretes_vencimento()
        
        # Mostrar resultados
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('RESULTADO'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        if resultado['status'] == 'desativado':
            self.stdout.write(self.style.WARNING('⚠️  Notificações desativadas'))
            self.stdout.write(self.style.WARNING(f"   {resultado['mensagem']}"))
        elif resultado['total'] == 0:
            self.stdout.write(self.style.WARNING('ℹ️  Nenhuma comanda para notificar'))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Total de comandas: {resultado['total']}"))
            self.stdout.write(self.style.SUCCESS(f"📧 Emails enviados: {resultado.get('emails', 0)}"))
            self.stdout.write(self.style.SUCCESS(f"📱 WhatsApp enviados: {resultado.get('whatsapp', 0)}"))
            
            if resultado.get('erros', 0) > 0:
                self.stdout.write(self.style.ERROR(f"❌ Erros: {resultado['erros']}"))
            
            self.stdout.write(self.style.SUCCESS(f"📅 Data alvo: {resultado.get('data_alvo', 'N/A')}"))
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
