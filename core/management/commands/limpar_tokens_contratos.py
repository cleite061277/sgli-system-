from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import ContratoDownloadToken


class Command(BaseCommand):
    help = 'Remove tokens de download de contratos expirados há mais de X dias'
    
    def add_arguments(self, parser):
        parser.add_argument('--dias', type=int, default=30, help='Dias após expiração para deletar')
        parser.add_argument('--dry-run', action='store_true', help='Simula sem deletar')
        parser.add_argument('--verbose', action='store_true', help='Mostra detalhes')
    
    def handle(self, *args, **options):
        dias = options['dias']
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        limite = timezone.now() - timedelta(days=dias)
        
        self.stdout.write(self.style.WARNING('🧹 LIMPEZA DE TOKENS DE DOWNLOAD'))
        self.stdout.write(f'📅 Tokens expirados há mais de {dias} dias serão removidos')
        
        if dry_run:
            self.stdout.write(self.style.NOTICE('🔍 MODO DRY-RUN (simulação)'))
        
        tokens_query = ContratoDownloadToken.objects.filter(expira_em__lt=limite)
        total_tokens = tokens_query.count()
        
        if total_tokens == 0:
            self.stdout.write(self.style.SUCCESS('✅ Nenhum token expirado encontrado'))
            return
        
        self.stdout.write(f'📊 {total_tokens} token(s) expirado(s) encontrado(s)')
        
        if verbose:
            for token in tokens_query[:10]:
                contrato = token.renovacao.nova_locacao.numero_contrato if token.renovacao.nova_locacao else 'N/A'
                self.stdout.write(f'• Token: {token.token.hex[:8]}... | Contrato: {contrato} | Acessos: {token.acessos}')
            if total_tokens > 10:
                self.stdout.write(f'... e mais {total_tokens - 10} tokens')
        
        if not dry_run:
            deletados = tokens_query.delete()
            self.stdout.write(self.style.SUCCESS(f'✅ {deletados[0]} token(s) deletado(s)!'))
        else:
            self.stdout.write(self.style.NOTICE(f'🔍 {total_tokens} SERIAM deletados'))
