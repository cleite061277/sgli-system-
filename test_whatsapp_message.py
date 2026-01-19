import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgli_project.settings')
django.setup()

from core.models import Comanda
from core.notifications.message_formatter import formatar_mensagem_whatsapp_comanda

# Pegar comanda
comanda = Comanda.objects.filter(numero_comanda='202601-0001').first()

if comanda:
    # Chamar DIRETAMENTE a função (não via classe)
    mensagem = formatar_mensagem_whatsapp_comanda(comanda)
    
    print("MENSAGEM GERADA (função direta):")
    print("="*64)
    print(mensagem)
    print("="*64)
    print()
    
    if "📝 COMENTÁRIOS" in mensagem:
        print("✅ Observações APARECEM (função direta)")
    else:
        print("❌ Observações NÃO APARECEM (função direta)")
else:
    print("❌ Comanda não encontrada")
