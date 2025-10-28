#!/usr/bin/env python
"""
DROPA todas as tabelas do app core e recria do zero
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgli_project.settings')
django.setup()

from django.db import connection

print("🔥 Iniciando RESET do banco de dados...")

with connection.cursor() as cursor:
    # Listar todas as tabelas do core
    cursor.execute("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'core_%'
        ORDER BY tablename;
    """)
    
    tables = cursor.fetchall()
    
    if tables:
        print(f"\n📊 Encontradas {len(tables)} tabelas do core:")
        for table in tables:
            print(f"  🗑️  Dropando: {table[0]}")
            cursor.execute(f'DROP TABLE IF EXISTS "{table[0]}" CASCADE;')
        
        print(f"\n✅ {len(tables)} tabelas dropadas com sucesso!")
    else:
        print("\n⚠️  Nenhuma tabela do core encontrada.")
    
    # Limpar django_migrations para o app core
    print("\n🧹 Limpando histórico de migrações...")
    cursor.execute("DELETE FROM django_migrations WHERE app = 'core';")
    print("✅ Histórico limpo!")

print("\n✅ RESET concluído! Banco pronto para novas migrações.")
