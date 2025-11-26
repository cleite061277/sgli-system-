#!/usr/bin/env python
"""
Verifica se todas as tabelas necessárias existem
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgli_project.settings')
django.setup()

from django.db import connection

print("🔍 Verificando tabelas no banco de dados...")

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        ORDER BY tablename;
    """)
    tables = cursor.fetchall()
    
    print(f"\n📊 Total de tabelas: {len(tables)}")
    print("\nTabelas existentes:")
    for table in tables:
        print(f"  ✅ {table[0]}")
    
    # Verificar se core_fiador existe
    table_names = [t[0] for t in tables]
    if 'core_fiador' not in table_names:
        print("\n⚠️  ATENÇÃO: Tabela 'core_fiador' NÃO existe!")
        print("   Será criada no próximo migrate.")
    else:
        print("\n✅ Tabela 'core_fiador' existe!")

print("\n✅ Verificação concluída")
