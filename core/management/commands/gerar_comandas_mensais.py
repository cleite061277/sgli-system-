from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta
from core.models import Locacao, Comanda, ConfiguracaoSistema, LogGeracaoComandas
import calendar


class Command(BaseCommand):
    help = 'Gera comandas mensais com vencimento individual por locação'
    
    def add_arguments(self, parser):
        parser.add_argument('--mes', type=str, help='Mês (YYYY-MM)')
        parser.add_argument('--dry-run', action='store_true', help='Simulação')
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Geração de Comandas Mensais'))
        self.stdout.write('=' * 60)
        
        # Mês de referência
        if options['mes']:
            try:
                mes_referencia = datetime.strptime(options['mes'], '%Y-%m').date().replace(day=1)
            except ValueError:
                self.stdout.write(self.style.ERROR('Formato inválido! Use YYYY-MM'))
                return
        else:
            hoje = timezone.now().date()
            mes_referencia = (hoje.replace(day=1) + relativedelta(months=1))
        
        self.stdout.write(f'\nMês de referência: {mes_referencia.strftime("%B/%Y")}')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('MODO SIMULAÇÃO'))
        
        self.stdout.write('')
        
        # Buscar locações ativas
        locacoes_ativas = Locacao.objects.filter(status='ativa')
        total = locacoes_ativas.count()
        
        self.stdout.write(f'Locações ativas: {total}')
        self.stdout.write('')
        
        if total == 0:
            self.stdout.write(self.style.WARNING('Nenhuma locação ativa'))
            return
        
        # Obter configuração padrão (fallback)
        config = ConfiguracaoSistema.get_config()
        dia_padrao = config.dia_vencimento_padrao
        
        criadas = 0
        duplicadas = 0
        erros = []
        
        for i, locacao in enumerate(locacoes_ativas, 1):
            try:
                # Obter dia de vencimento específico da locação
                dia_vencimento = getattr(locacao, 'dia_vencimento', None) or dia_padrao
                
                # Ajustar para último dia do mês se necessário
                ultimo_dia = calendar.monthrange(mes_referencia.year, mes_referencia.month)[1]
                if dia_vencimento > ultimo_dia:
                    dia_vencimento = ultimo_dia
                
                data_vencimento = mes_referencia.replace(day=dia_vencimento)
                
                self.stdout.write(
                    f'[{i}/{total}] {locacao} - Venc: {data_vencimento.strftime("%d/%m/%Y")}'
                )
                
                # Verificar duplicata
                if Comanda.objects.filter(locacao=locacao, mes_referencia=mes_referencia).exists():
                    self.stdout.write(self.style.WARNING('  Já existe'))
                    duplicadas += 1
                    continue
                
                # Valores
                valor_aluguel = locacao.valor_aluguel
                valor_condominio = getattr(locacao, 'valor_condominio', 0) or 0
                valor_iptu = getattr(locacao, 'valor_iptu', 0) or 0
                
                if not options['dry_run']:
                    comanda = Comanda.objects.create(
                        locacao=locacao,
                        mes_referencia=mes_referencia,
                        ano_referencia=mes_referencia.year,
                        data_vencimento=data_vencimento,
                        valor_aluguel=valor_aluguel,
                        valor_condominio=valor_condominio,
                        valor_iptu=valor_iptu,
                        valor_administracao=0,
                        outros_creditos=0,
                        outros_debitos=0,
                        multa=0,
                        juros=0,
                        desconto=0,
                        status='pendente',
                        observacoes=f'Gerada automaticamente em {timezone.now().strftime("%d/%m/%Y %H:%M")}'
                    )
                    valor_total = comanda.valor_aluguel + comanda.valor_condominio + comanda.valor_iptu
                    self.stdout.write(self.style.SUCCESS(f'  Criada: R$ {valor_total:.2f}'))
                else:
                    valor_total = valor_aluguel + valor_condominio + valor_iptu
                    self.stdout.write(self.style.SUCCESS(f'  [SIM] R$ {valor_total:.2f}'))
                
                criadas += 1
                
            except Exception as e:
                erro_msg = f'Erro na locação {locacao.id}: {str(e)}'
                self.stdout.write(self.style.ERROR(f'  {erro_msg}'))
                erros.append(erro_msg)
        
        # Resumo
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('RESUMO')
        self.stdout.write('=' * 60)
        self.stdout.write(f'Criadas: {criadas}')
        self.stdout.write(f'Duplicadas: {duplicadas}')
        self.stdout.write(f'Processadas: {total}')
        
        if erros:
            self.stdout.write(self.style.ERROR(f'Erros: {len(erros)}'))
        
        # Log
        if not options['dry_run']:
            LogGeracaoComandas.objects.create(
                mes_referencia=mes_referencia,
                comandas_geradas=criadas,
                comandas_duplicadas=duplicadas,
                locacoes_processadas=total,
                sucesso=len(erros) == 0,
                mensagem=f'{criadas} comandas criadas com vencimentos individualizados',
                erro='\n'.join(erros) if erros else '',
                executado_por='manual'
            )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('CONCLUÍDO'))
