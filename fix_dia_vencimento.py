#!/usr/bin/env python
"""
Script para corrigir TODOS os erros no models.py do SGLI
Autor: Claude (Anthropic)
Data: 06/10/2025

CORREÇÕES:
1. Remove vírgula extra no campo dia_vencimento (Locacao)
2. Remove validadores incorretos no campo mes_referencia (Comanda)

INSTRUÇÕES:
1. Faça backup: cp core/models.py core/models.py.backup
2. Execute: python fix_models_completo.py
3. Execute: python manage.py makemigrations
4. Execute: python manage.py migrate
"""

import re
import sys
from pathlib import Path


def corrigir_models_py():
    """Corrige todos os erros identificados no models.py"""
    
    models_path = Path('core/models.py')
    
    if not models_path.exists():
        print("❌ Arquivo core/models.py não encontrado!")
        print("Execute este script da raiz do projeto (onde está manage.py)")
        sys.exit(1)
    
    # Fazer backup
    backup_path = models_path.parent / 'models.py.backup'
    print(f"📦 Criando backup em: {backup_path}")
    
    with open(models_path, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print("✅ Backup criado!")
    print()
    
    correcoes_feitas = 0
    
    # CORREÇÃO 1: Remover vírgula extra no dia_vencimento
    print("🔧 Correção 1: Removendo vírgula extra em dia_vencimento...")
    
    padrao_vencimento = r"(dia_vencimento = models\.IntegerField\([^)]+\)\s*),(\s*\n)"
    
    if re.search(padrao_vencimento, conteudo):
        conteudo = re.sub(padrao_vencimento, r"\1\2", conteudo)
        print("   ✅ Vírgula removida!")
        correcoes_feitas += 1
    else:
        print("   ℹ️  Já estava correto ou não encontrado")
    
    # CORREÇÃO 2: Remover validadores incorretos do mes_referencia
    print("🔧 Correção 2: Corrigindo campo mes_referencia...")
    
    # Padrão antigo (com validadores errados)
    padrao_mes_antigo = r"""mes_referencia = models\.DateField\(
        validators=\[MinValueValidator\(1\), MaxValueValidator\(12\)\],
        verbose_name=_\('Mês de Referência'\),
        help_text=_\('Mês de referência da cobrança \(1-12\)'\)
    \)"""
    
    # Novo padrão (sem validadores)
    substituicao_mes = """mes_referencia = models.DateField(
        verbose_name=_('Mês de Referência'),
        help_text=_('Primeiro dia do mês de referência (formato YYYY-MM-01)')
    )"""
    
    if re.search(r"mes_referencia = models\.DateField\(\s*validators=", conteudo):
        conteudo = re.sub(padrao_mes_antigo, substituicao_mes, conteudo)
        print("   ✅ Validadores removidos!")
        correcoes_feitas += 1
    else:
        print("   ℹ️  Já estava correto ou não encontrado")
    
    # Salvar arquivo corrigido
    if correcoes_feitas > 0:
        with open(models_path, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        print()
        print("=" * 70)
        print(f"✅ {correcoes_feitas} correção(ões) aplicada(s) com sucesso!")
        print("=" * 70)
        print()
        print("📋 PRÓXIMOS PASSOS:")
        print("   1. python manage.py makemigrations")
        print("   2. python manage.py migrate")
        print("   3. Teste no admin: http://localhost:8000/admin/")
        print()
        print("💡 DICA: Use formato MM/YYYY (ex: 10/2025) para o mês de referência")
        
    else:
        print()
        print("=" * 70)
        print("ℹ️  Nenhuma correção necessária - arquivo já estava correto!")
        print("=" * 70)
    
    return correcoes_feitas > 0


def verificar_sintaxe():
    """Verifica se o arquivo tem sintaxe Python válida"""
    print()
    print("🔍 Verificando sintaxe do arquivo...")
    
    try:
        import py_compile
        py_compile.compile('core/models.py', doraise=True)
        print("✅ Sintaxe Python válida!")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Erro de sintaxe encontrado:")
        print(f"   {e}")
        return False


if __name__ == '__main__':
    print("=" * 70)
    print("🔧 CORREÇÃO COMPLETA DO MODELS.PY - SGLI")
    print("=" * 70)
    print()
    
    # Executar correções
    sucesso = corrigir_models_py()
    
    if sucesso:
        # Verificar sintaxe
        if verificar_sintaxe():
            print()
            print("=" * 70)
            print("✅ TUDO PRONTO! Arquivo corrigido e sintaxe válida!")
            print("=" * 70)
        else:
            print()
            print("⚠️  Houve um problema - restaure o backup:")
            print("   cp core/models.py.backup core/models.py")
