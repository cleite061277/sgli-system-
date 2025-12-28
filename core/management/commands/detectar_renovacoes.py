"""
Management command para detectar e criar propostas de renovação automaticamente.
Roda diariamente via APScheduler.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from core.models import Locacao, RenovacaoContrato
from core.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Detecta contratos próximos do vencimento e cria propostas de renovação'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=90,
            help='Dias de antecedência para detectar vencimentos (padrão: 90)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula execução sem criar renovações'
        )
        
        parser.add_argument(
            '--aumento',
            type=float,
            default=0.0,
            help='Percentual de aumento padrão (ex: 10.0 para 10%)'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        dias_antecedencia = options['dias']
        percentual_aumento = Decimal(str(options['aumento']))
        
        hoje = timezone.now().date()
        data_limite = hoje + timedelta(days=dias_antecedencia)
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*70}'))
        self.stdout.write(self.style.SUCCESS(f'🔄 DETECÇÃO DE RENOVAÇÕES - {hoje}'))
        self.stdout.write(self.style.SUCCESS(f'{"="*70}\n'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODO DRY-RUN (não criará renovações)\n'))
        
        # ========================================
        # 1. BUSCAR CONTRATOS PRÓXIMOS DO VENCIMENTO
        # ========================================
        
        self.stdout.write('📋 Buscando contratos que vencem nos próximos {} dias...\n'.format(dias_antecedencia))
        
        # Contratos ativos que vencem em até X dias
        # E que ainda NÃO possuem proposta de renovação
        locacoes_vencendo = Locacao.objects.filter(
            status='ACTIVE',
            data_fim__gte=hoje,
            data_fim__lte=data_limite,
        ).exclude(
            # Excluir locações que já têm renovação em andamento
            propostas_renovacao__status__in=[
                'rascunho',
                'pendente_proprietario',
                'pendente_locatario',
                'aprovada'
            ]
        ).select_related('imovel', 'locatario', 'imovel__locador')
        
        total = locacoes_vencendo.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING('ℹ️  Nenhum contrato encontrado para renovação.\n'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'✅ Encontrados {total} contrato(s)\n'))
        
        # ========================================
        # 2. CRIAR PROPOSTAS DE RENOVAÇÃO
        # ========================================
        
        stats = {
            'criadas': 0,
            'erros': 0,
            'notificacoes_enviadas': 0,
        }
        
        for locacao in locacoes_vencendo:
            try:
                dias_restantes = (locacao.data_fim - hoje).days
                
                self.stdout.write(
                    f'\n📌 Processando: {locacao.numero_contrato} '
                    f'({locacao.imovel.endereco_completo})'
                )
                self.stdout.write(f'   Locatário: {locacao.locatario.nome_razao_social}')
                self.stdout.write(f'   Vencimento: {locacao.data_fim.strftime("%d/%m/%Y")} ({dias_restantes} dias)')
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('   [DRY-RUN] Renovação seria criada'))
                    stats['criadas'] += 1
                    continue
                
                # ========================================
                # CALCULAR NOVA PROPOSTA
                # ========================================
                
                # Datas da nova vigência (1 dia após vencimento)
                nova_data_inicio = locacao.data_fim + timedelta(days=1)
                nova_data_fim = nova_data_inicio + timedelta(days=365)  # 12 meses
                
                # Valor com aumento (se especificado)
                if percentual_aumento > 0:
                    novo_valor = locacao.valor_aluguel * (1 + percentual_aumento / 100)
                else:
                    # Manter mesmo valor (admin ajusta depois)
                    novo_valor = locacao.valor_aluguel
                
                # Criar proposta de renovação
                renovacao = RenovacaoContrato.objects.create(
                    locacao_original=locacao,
                    nova_data_inicio=nova_data_inicio,
                    nova_data_fim=nova_data_fim,
                    nova_duracao_meses=12,
                    novo_valor_aluguel=novo_valor,
                    
                    # Copiar garantias do contrato atual
                    novo_tipo_garantia=locacao.tipo_garantia,
                    novo_fiador=locacao.fiador_garantia,
                    nova_caucao_meses=locacao.caucao_quantidade_meses,
                    nova_seguro_apolice=locacao.seguro_apolice,
                    
                    # Status inicial
                    status='rascunho',
                    
                    # Observações
                    observacoes=f'Renovação detectada automaticamente em {hoje.strftime("%d/%m/%Y")}. '
                                f'Revisar valores antes de enviar ao proprietário.'
                )
                
                self.stdout.write(self.style.SUCCESS(f'   ✅ Renovação criada: ID {renovacao.id}'))
                self.stdout.write(f'   💰 Valor proposto: R$ {novo_valor:,.2f}')
                
                stats['criadas'] += 1
                
                # ========================================
                # NOTIFICAR ADMINISTRADOR
                # ========================================
                
                try:
                    EmailService.notificar_admin_nova_renovacao(renovacao)
                    self.stdout.write(self.style.SUCCESS('   📧 Admin notificado'))
                    stats['notificacoes_enviadas'] += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  Erro ao notificar admin: {e}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Erro: {e}'))
                stats['erros'] += 1
                logger.error(f"Erro ao processar locação {locacao.id}: {e}", exc_info=True)
        
        # ========================================
        # 3. RESUMO
        # ========================================
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*70}'))
        self.stdout.write(self.style.SUCCESS('📊 RESUMO DA EXECUÇÃO'))
        self.stdout.write(self.style.SUCCESS(f'{"="*70}'))
        self.stdout.write(f'✅ Renovações criadas: {stats["criadas"]}')
        self.stdout.write(f'📧 Notificações enviadas: {stats["notificacoes_enviadas"]}')
        self.stdout.write(f'❌ Erros: {stats["erros"]}')
        self.stdout.write(self.style.SUCCESS(f'{"="*70}\n'))
        
        if not dry_run and stats['criadas'] > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n💡 Próximo passo: Acesse o admin para revisar as '
                    f'{stats["criadas"]} proposta(s) criada(s) '
                    f'e enviar aos proprietários.\n'
                )
            )
