"""
Comando Django para resetar tabelas do core
Uso: python manage.py reset_core_tables
"""
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Dropa e recria todas as tabelas do app core'

    def handle(self, *args, **options):
        self.stdout.write('🔥 Resetando tabelas do core...')
        
        with connection.cursor() as cursor:
            # Desabilitar constraints temporariamente
            cursor.execute('SET CONSTRAINTS ALL DEFERRED;')
            
            # Listar tabelas do core
            cursor.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename LIKE 'core_%'
            """)
            
            tables = cursor.fetchall()
            
            if tables:
                self.stdout.write(f'Encontradas {len(tables)} tabelas')
                for table in tables:
                    self.stdout.write(f'  Dropando: {table[0]}')
                    cursor.execute(f'DROP TABLE IF EXISTS "{table[0]}" CASCADE')
                
                # Limpar histórico de migrações
                cursor.execute("DELETE FROM django_migrations WHERE app = 'core'")
                
                self.stdout.write(self.style.SUCCESS('✅ Reset concluído!'))
            else:
                self.stdout.write('⚠️  Nenhuma tabela encontrada')
