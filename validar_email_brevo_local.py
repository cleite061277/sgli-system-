#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
VALIDAÇÃO EMAIL BREVO - HABITAT PRO
═══════════════════════════════════════════════════════════════
Script simplificado para testar configuração Brevo localmente

Uso: python3 validar_email_brevo_local.py

Pré-requisitos:
- BREVO_API_KEY no arquivo .env
- settings.py já modificado para Brevo
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import django

# Configurar path para Django
BASE_DIR = os.path.expanduser('~/sgli_system')
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgli_project.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ ERRO ao configurar Django: {e}")
    sys.exit(1)

from django.core.mail import send_mail
from django.conf import settings

print("\n" + "="*70)
print("🔍 VALIDAÇÃO BREVO - HABITAT PRO")
print("="*70)

# 1. Verificar Backend
print("\n1️⃣ Verificando backend de email...")
backend = settings.EMAIL_BACKEND
print(f"   Backend: {backend}")

if "sendinblue" in backend.lower():
    print("   ✅ Backend Brevo/Sendinblue detectado")
elif "sendgrid" in backend.lower():
    print("   ⚠️  Backend ainda está como SendGrid!")
    print("   💡 Execute: bash modificar_settings_brevo.sh")
    sys.exit(1)
else:
    print(f"   ⚠️  Backend: {backend}")

# 2. Verificar API Key
print("\n2️⃣ Verificando BREVO_API_KEY...")
brevo_key = os.environ.get('BREVO_API_KEY')

if brevo_key:
    masked = brevo_key[:15] + "..." + brevo_key[-10:]
    print(f"   API Key: {masked}")
    
    if brevo_key.startswith('xkeysib-'):
        print("   ✅ Formato válido")
    else:
        print("   ⚠️  Formato inesperado")
else:
    print("   ❌ BREVO_API_KEY não encontrada no ambiente!")
    print("   💡 Adicione ao arquivo .env")
    sys.exit(1)

# 3. Verificar remetente
print("\n3️⃣ Verificando email remetente...")
from_email = settings.DEFAULT_FROM_EMAIL
print(f"   Remetente: {from_email}")

if '@' in from_email:
    print("   ✅ Email válido")
    print("   ⚠️  Certifique-se que está verificado no Brevo!")
else:
    print("   ❌ Email inválido!")
    sys.exit(1)

# 4. Solicitar email de destino
print("\n" + "="*70)
print("📧 TESTE DE ENVIO")
print("="*70)

email_destino = input("\n📧 Digite seu email para teste: ").strip()

if not email_destino or '@' not in email_destino:
    print("❌ Email inválido!")
    sys.exit(1)

print(f"\n🎯 Enviando email de teste para: {email_destino}")
print(f"📤 Remetente: {from_email}")
print("⏳ Aguarde...")

# HTML do email de teste
html_content = """
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; color: white;">
        <h1 style="margin: 0 0 20px 0;">✅ Teste Brevo - HABITAT PRO</h1>
        <p style="font-size: 16px; line-height: 1.6;">
            Este é um email de teste da migração <strong>SendGrid → Brevo</strong>.
        </p>
        <p style="font-size: 14px; margin-top: 30px; opacity: 0.9;">
            Se você recebeu este email, a configuração está funcionando! 🎉
        </p>
        <hr style="border: 1px solid rgba(255,255,255,0.3); margin: 20px 0;">
        <p style="font-size: 12px; opacity: 0.8;">
            <strong>HABITAT PRO v1.0</strong><br>
            Sistema de Gestão Imobiliária<br>
            A&C Imóveis e Sistemas Imobiliários | Paranaguá - PR<br>
            Tel: 41 3723-2032
        </p>
    </div>
</body>
</html>
"""

try:
    resultado = send_mail(
        subject='✅ Teste Brevo - HABITAT PRO',
        message='Se você vê isso, seu cliente não suporta HTML',
        from_email=from_email,
        recipient_list=[email_destino],
        html_message=html_content,
        fail_silently=False
    )
    
    print("\n" + "="*70)
    print("✅ EMAIL ENVIADO COM SUCESSO!")
    print("="*70)
    print(f"\n📊 Resultado: {resultado} email(s) enviado(s)")
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("\n1️⃣ Verifique sua caixa de entrada:")
    print(f"   📧 {email_destino}")
    print("   📁 Verifique também SPAM/Lixo Eletrônico")
    
    print("\n2️⃣ Validações no email recebido:")
    print("   ✅ Assunto: 'Teste Brevo - HABITAT PRO'")
    print("   ✅ Formatação HTML com fundo roxo gradiente")
    print("   ✅ Logo e informações da A&C Imóveis")
    
    print("\n3️⃣ Verificar Brevo Dashboard:")
    print("   🌐 https://app.brevo.com/statistics/email")
    print("   📈 Email deve aparecer como 'Delivered'")
    
    print("\n4️⃣ Se tudo OK:")
    print("   ✅ Configuração validada!")
    print("   🚀 Próximo: Adicionar variável no Railway")
    print("   📝 Depois: Commit e deploy")
    
    print("\n" + "="*70)
    print("✅ VALIDAÇÃO LOCAL CONCLUÍDA")
    print("="*70 + "\n")
    
except Exception as e:
    print("\n" + "="*70)
    print("❌ ERRO AO ENVIAR EMAIL!")
    print("="*70)
    print(f"\n🔴 Tipo: {type(e).__name__}")
    print(f"🔴 Mensagem: {str(e)}")
    
    erro_str = str(e).lower()
    
    print("\n🔍 DIAGNÓSTICO:")
    
    if '401' in erro_str or 'unauthorized' in erro_str:
        print("   🔑 API Key inválida ou incorreta")
        print("   💡 Verifique BREVO_API_KEY no .env")
        print("   💡 Regenere no Brevo se necessário")
        
    elif '422' in erro_str or 'invalid sender' in erro_str:
        print("   📧 Email remetente não verificado")
        print(f"   📧 Problemático: {from_email}")
        print("   💡 Verifique em: https://app.brevo.com/settings/senders")
        
    elif 'timeout' in erro_str:
        print("   ⏱️  Timeout de conexão")
        print("   💡 Verifique sua internet")
        print("   💡 Tente novamente em 1 minuto")
        
    else:
        print("   ❓ Erro desconhecido")
        print("   💡 Consulte: https://developers.brevo.com/docs")
    
    print("\n🔄 NÃO faça deploy até resolver o erro!")
    print("\n" + "="*70 + "\n")
    sys.exit(1)
