#!/usr/bin/env python3
"""
Teste de concorrência para SequenceCounter
Executa 20 chamadas paralelas e verifica unicidade/sequencialidade
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/usuario/sgli_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgli_project.settings')
django.setup()

from multiprocessing import Pool
from core.models import SequenceCounter

def call_get_next(i):
    """Chama get_next e retorna resultado"""
    try:
        return SequenceCounter.get_next('concurrent-test-202511')
    except Exception as e:
        print(f"❌ Erro no worker {i}: {e}")
        return None

if __name__ == '__main__':
    print("🧪 TESTE DE CONCORRÊNCIA: SequenceCounter")
    print("  - 20 workers paralelos")
    print("  - Verificando unicidade e sequencialidade")
    print("")
    
    # Limpar dados de teste anteriores
    SequenceCounter.objects.filter(prefix='concurrent-test-202511').delete()
    print("✅ Dados de teste limpos")
    
    # Executar em paralelo
    with Pool(8) as pool:
        results = pool.map(call_get_next, range(20))
    
    # Filtrar None (erros)
    results = [r for r in results if r is not None]
    
    print(f"\n📊 RESULTADOS:")
    print(f"  - Total obtido: {len(results)}/20")
    print(f"  - Valores: {sorted(results)}")
    print(f"  - Únicos: {len(set(results))}")
    
    # Verificações
    if len(results) == 20:
        print("  ✅ Todos os workers obtiveram número")
    else:
        print(f"  ⚠️ {20-len(results)} workers falharam")
    
    if len(set(results)) == len(results):
        print("  ✅ Todos os números são únicos")
    else:
        print(f"  ❌ DUPLICATAS DETECTADAS!")
        
    if sorted(results) == list(range(1, 21)):
        print("  ✅ Sequência perfeita (1-20)")
    else:
        print("  ⚠️ Sequência com gaps ou desordem")
    
    # Limpar teste
    SequenceCounter.objects.filter(prefix='concurrent-test-202511').delete()
    print("\n✅ Teste concluído e dados limpos")
