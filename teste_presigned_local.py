"""
Teste local do método get_presigned_url()
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgli_project.settings')

import django
django.setup()

from core.models_inspection import InspectionPDF

print("════════════════════════════════════════════════════════════")
print("🧪 TESTE LOCAL - PRESIGNED URLs")
print("════════════════════════════════════════════════════════════")
print("")

# Buscar PDFs existentes
pdfs = InspectionPDF.objects.all()

if pdfs.exists():
    pdf = pdfs.first()
    print(f"📄 PDF Teste: {pdf.arquivo.name}")
    print("")
    
    # Testar geração de presigned URL
    print("1️⃣ Gerando presigned URL...")
    try:
        url = pdf.get_presigned_url(expiration=3600)  # 1 hora para teste
        
        if url:
            print("   ✅ Presigned URL gerada com sucesso!")
            print(f"   URL: {url[:80]}...")
            print("")
            print("   ℹ️ Esta URL é válida por 1 hora")
            print("   ℹ️ Em produção será válida por 7 dias")
        else:
            print("   ❌ Falha ao gerar URL")
            
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
else:
    print("ℹ️ Nenhum PDF encontrado no banco local")
    print("   (Normal se não testou localmente)")

print("")
print("════════════════════════════════════════════════════════════")
