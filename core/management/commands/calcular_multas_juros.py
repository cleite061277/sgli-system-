from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from core.models import Comanda, ConfiguracaoSistema


class Command(BaseCommand):
    help = 'Calcula e aplica multas e juros em comandas vencidas'
    
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Simulação')
    
    def handle(self, *args, **options):
        self.stdout.write('Cálculo de Multas e Juros')
        self.stdout.write('=' * 60)
        
        hoje = timezone.now().date()
        config = ConfiguracaoSistema.get_config()
        
        self.stdout.write(f'\nData: {hoje.strftime("%d/%m/%Y")}')
        self.stdout.write(f'Multa: {config.percentual_multa}%')
        self.stdout.write(f'Juros: {config.percentual_juros_mensal}% ao mês')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\nSIMULAÇÃO'))
        
        # Buscar comandas vencidas
        comandas = Comanda.objects.filter(
            status__in=['pendente', 'vencida'],
            data_vencimento__lt=hoje
        )
        
        total = comandas.count()
        self.stdout.write(f'\nComandas vencidas: {total}\n')
        
        if total == 0:
            self.stdout.write('Nenhuma comanda vencida')
            return
        
        atualizadas = 0
        valor_total_multas = Decimal('0.00')
        valor_total_juros = Decimal('0.00')
        
        for comanda in comandas:
            dias_atraso = (hoje - comanda.data_vencimento).days
            
            if dias_atraso <= 0:
                continue
            
            # Calcular multa (% do aluguel)
            multa = (comanda.valor_aluguel * config.percentual_multa / 100).quantize(Decimal('0.01'))
            
            # Calcular juros (% ao mês pro-rata)
            juros_diario = config.percentual_juros_mensal / 30
            juros = (comanda.valor_aluguel * juros_diario * dias_atraso / 100).quantize(Decimal('0.01'))
            
            self.stdout.write(
                f'{comanda.numero_comanda} | Atraso: {dias_atraso}d | '
                f'Multa: R$ {multa} | Juros: R$ {juros}'
            )
            
            if not options['dry_run']:
                comanda.multa = multa
                comanda.juros = juros
                comanda.status = 'vencida'
                comanda.save(update_fields=['multa', 'juros', 'status'])
            
            valor_total_multas += multa
            valor_total_juros += juros
            atualizadas += 1
        
        # Resumo
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('RESUMO')
        self.stdout.write('=' * 60)
        self.stdout.write(f'Comandas processadas: {atualizadas}')
        self.stdout.write(f'Total em multas: R$ {valor_total_multas}')
        self.stdout.write(f'Total em juros: R$ {valor_total_juros}')
        self.stdout.write(f'Total geral: R$ {valor_total_multas + valor_total_juros}')
        
        if not options['dry_run']:
            self.stdout.write('\nValores aplicados no banco de dados')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('CONCLUÍDO'))
