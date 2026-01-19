#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "🧪 TESTE COMPLETO - SISTEMA DE VISTORIAS"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "1️⃣ CREDENCIAIS RAILWAY (verificar se Railway foi atualizado):"
echo ""
echo "   ⚠️  AÇÃO MANUAL NECESSÁRIA:"
echo "   • Acesse: https://railway.app"
echo "   • romantic-liberation → Variables"
echo "   • Verificar se R2_ACCESS_KEY_ID começa com: 47a0692454..."
echo "   • Se NÃO, atualizar manualmente"
echo ""

echo "2️⃣ CREDENCIAIS LOCAIS:"
echo "   ✅ Access Key: $(grep R2_ACCESS_KEY_ID railway_env_variables.txt | cut -d= -f2 | cut -c1-20)..."
echo "   ✅ Bucket: habitat-pro-storage"
echo "   ✅ Endpoint: ...4e46dfe4280b9b3fd2503d1967761c38.r2..."
echo ""

echo "3️⃣ TESTE DE CONEXÃO:"
python << 'PYEOF'
import boto3

ACCESS_KEY = "47a0692454108b4ed5dadb44708ea0e1"
SECRET_KEY = "9f878dad68967e8e410adb714d34da25798cb61d76be41976aa830cac400cec4"
ENDPOINT = "https://4e46dfe4280b9b3fd2503d1967761c38.r2.cloudflarestorage.com"
BUCKET = "habitat-pro-storage"

try:
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY, 
                      aws_secret_access_key=SECRET_KEY,
                      endpoint_url=ENDPOINT, region_name='auto')
    response = s3.list_objects_v2(Bucket=BUCKET, MaxKeys=1)
    print("   ✅ Cloudflare R2 acessível")
    
    # Verificar se há objetos
    if 'Contents' in response:
        print(f"   ✅ Bucket contém objetos: {len(response['Contents'])}")
    else:
        print("   ℹ️  Bucket vazio (normal se sem vistorias)")
        
except Exception as e:
    print(f"   ❌ ERRO: {e}")
PYEOF

echo ""
echo "4️⃣ PRÓXIMO PASSO - TESTAR NO MOBILE:"
echo ""
echo "   A. ADMIN:"
echo "      1. https://romantic-liberation-production.up.railway.app/admin"
echo "      2. Login com suas credenciais"
echo "      3. Vistorias → Adicionar"
echo ""
echo "   B. CRIAR VISTORIA TESTE:"
echo "      • Contrato: Selecione qualquer"
echo "      • Título: 'Teste Credenciais Corrigidas'"
echo "      • Inspector: 'Cícero'"
echo "      • Salvar"
echo ""
echo "   C. TESTAR MOBILE:"
echo "      • Copiar link público"
echo "      • Abrir no celular"
echo "      • Tirar 1-2 fotos"
echo "      • Verificar se upload funciona SEM ERROS"
echo "      • Finalizar vistoria"
echo "      • Verificar se PDF foi gerado"
echo ""

echo "════════════════════════════════════════════════════════════"
echo "✅ PREPARAÇÃO CONCLUÍDA"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  CRÍTICO: Verificar se Railway foi atualizado!"
echo "   Se R2_ACCESS_KEY_ID no Railway ainda for 'k7a0692...',"
echo "   você DEVE atualizar manualmente para '47a0692...'"
echo ""
