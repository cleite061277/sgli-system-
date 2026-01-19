"""
Script para verificar data de expiração do token R2
Executar mensalmente para acompanhamento
"""
from datetime import datetime, timedelta

TOKEN_EXPIRA_EM = datetime(2027, 1, 12)  # ← ATUALIZADO: 12/01/2027
hoje = datetime.now()
dias_restantes = (TOKEN_EXPIRA_EM - hoje).days

print("════════════════════════════════════════════════════════════")
print("🔐 VERIFICAÇÃO TOKEN CLOUDFLARE R2")
print("════════════════════════════════════════════════════════════")
print(f"Data de hoje: {hoje.strftime('%d/%m/%Y')}")
print(f"Token expira em: {TOKEN_EXPIRA_EM.strftime('%d/%m/%Y')}")
print(f"Dias restantes: {dias_restantes} dias")
print("")

if dias_restantes <= 0:
    print("🚨 TOKEN EXPIRADO! Renovar imediatamente!")
    print("   • Acesse: https://dash.cloudflare.com")
    print("   • R2 → API Tokens → Renovar")
elif dias_restantes <= 30:
    print("⚠️  TOKEN EXPIRA EM MENOS DE 30 DIAS!")
    print("   • Ação recomendada: Renovar agora")
    print("   • Siga instruções em RENOVACAO_R2_2027.md")
elif dias_restantes <= 60:
    print("⏰ Token expira em breve (menos de 60 dias)")
    print("   • Planejar renovação para este mês")
else:
    print("✅ Token válido - Sem ação necessária")
    print(f"   • Verificar novamente em {(hoje + timedelta(days=30)).strftime('%d/%m/%Y')}")

print("")
print("📋 CREDENCIAIS ATUAIS:")
print("   • Token: Habitat Pro - Token")
print("   • Created: 12/01/2026")
print("   • Expires: 12/01/2027")
print("")
print("════════════════════════════════════════════════════════════")
