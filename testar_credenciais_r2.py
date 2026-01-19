"""
Teste de conexão R2 com as credenciais do documento
"""
import boto3

# Credenciais do documento (Image 2)
ACCESS_KEY = "47a0692454108b4ed5dadb44708ea0e1"
SECRET_KEY = "9f878dad68967e8e410adb714d34da25798cb61d76be41976aa830cac400cec4"
ENDPOINT = "https://4e46dfe4280b9b3fd2503d1967761c38.r2.cloudflarestorage.com"
BUCKET = "habitat-pro-storage"

print("Testando credenciais do documento...")
print(f"Access Key: {ACCESS_KEY[:20]}...")
print(f"Endpoint: {ENDPOINT}")
print("")

try:
    s3 = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        endpoint_url=ENDPOINT,
        region_name='auto'
    )
    
    # Tentar listar objetos
    response = s3.list_objects_v2(Bucket=BUCKET, MaxKeys=1)
    print("✅ CONEXÃO BEM-SUCEDIDA!")
    print(f"Bucket existe e é acessível")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    print("\nCredenciais do documento estão INCORRETAS")
