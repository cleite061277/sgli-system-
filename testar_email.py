#!/usr/bin/env python3
"""
Script de Teste de Email - HABITAT PRO
Testa se as credenciais de email estão funcionando corretamente
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/home/claude/sgli_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgli_project.settings')
django.setup()

from django.core.mail import send_mail, EmailMessage
from django.conf import settings

def teste_email_simples():
    """Teste simples com send_mail"""
    print("═" * 60)
    print("📧 TESTE 1: Envio Simples")
    print("═" * 60)
    print()
    
    try:
        resultado = send_mail(
            subject='Teste HABITAT PRO - Email Simples',
            message='Este é um email de teste do sistema HABITAT PRO.\n\nSe você recebeu esta mensagem, o envio de email está funcionando corretamente!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Envia para si mesmo
            fail_silently=False,
        )
        
        if resultado == 1:
            print("✅ Email enviado com sucesso!")
            print(f"   De: {settings.DEFAULT_FROM_EMAIL}")
            print(f"   Para: {settings.EMAIL_HOST_USER}")
            return True
        else:
            print("❌ Falha no envio (resultado = 0)")
            return False
            
    except Exception as e:
        print(f"❌ ERRO ao enviar email: {e}")
        return False

def teste_email_html():
    """Teste com email HTML formatado"""
    print()
    print("═" * 60)
    print("📧 TESTE 2: Envio HTML Formatado")
    print("═" * 60)
    print()
    
    try:
        html_content = """
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; padding: 30px; text-align: center; border-radius: 10px;">
                    <h1>🏠 HABITAT PRO</h1>
                    <p style="font-size: 18px;">Sistema de Gestão Imobiliária</p>
                </div>
                <div style="padding: 30px; background: #f8f9fa; margin-top: 20px; border-radius: 10px;">
                    <h2 style="color: #667eea;">Teste de Email HTML</h2>
                    <p>Se você está vendo esta mensagem formatada, o sistema de email está <strong>100% funcional</strong>!</p>
                    <ul>
                        <li>✅ Conexão SMTP estabelecida</li>
                        <li>✅ Autenticação bem-sucedida</li>
                        <li>✅ HTML renderizado corretamente</li>
                    </ul>
                </div>
                <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                    <p>HABITAT PRO - Sistema de Gestão Imobiliária © 2025</p>
                </div>
            </body>
        </html>
        """
        
        email = EmailMessage(
            subject='Teste HABITAT PRO - Email HTML',
            body='Seu cliente de email não suporta HTML. Veja a versão web.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.EMAIL_HOST_USER],
        )
        
        email.content_subtype = 'html'
        email.body = html_content
        email.send()
        
        print("✅ Email HTML enviado com sucesso!")
        print(f"   De: {settings.DEFAULT_FROM_EMAIL}")
        print(f"   Para: {settings.EMAIL_HOST_USER}")
        return True
        
    except Exception as e:
        print(f"❌ ERRO ao enviar email HTML: {e}")
        return False

def exibir_configuracoes():
    """Exibe configurações de email atuais"""
    print()
    print("═" * 60)
    print("⚙️  CONFIGURAÇÕES ATUAIS DE EMAIL")
    print("═" * 60)
    print()
    print(f"Backend:        {settings.EMAIL_BACKEND}")
    print(f"Host:           {settings.EMAIL_HOST}")
    print(f"Porta:          {settings.EMAIL_PORT}")
    print(f"TLS:            {settings.EMAIL_USE_TLS}")
    print(f"Usuário:        {settings.EMAIL_HOST_USER}")
    print(f"Senha:          {'*' * 8} (configurada)")
    print(f"From Default:   {settings.DEFAULT_FROM_EMAIL}")
    print()

def main():
    """Função principal"""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  🏠 HABITAT PRO - TESTE DE CREDENCIAIS DE EMAIL  ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    # Exibir configurações
    exibir_configuracoes()
    
    input("Pressione ENTER para iniciar os testes...")
    
    # Executar testes
    teste1 = teste_email_simples()
    teste2 = teste_email_html()
    
    # Relatório final
    print()
    print("═" * 60)
    print("📊 RELATÓRIO FINAL")
    print("═" * 60)
    print()
    
    if teste1 and teste2:
        print("✅ TODOS OS TESTES PASSARAM!")
        print()
        print("🎉 Sistema de email está 100% funcional!")
        print()
        print("Você deve ter recebido 2 emails em:")
        print(f"   📧 {settings.EMAIL_HOST_USER}")
        print()
        print("Próximos passos:")
        print("   1. Verificar caixa de entrada")
        print("   2. Verificar spam (caso não apareça)")
        print("   3. Testar envio de comandas e recibos no admin")
        return 0
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print()
        print("Possíveis causas:")
        print("   1. Senha de app do Gmail incorreta")
        print("   2. Autenticação de 2 fatores não configurada")
        print("   3. Bloqueio de 'apps menos seguros'")
        print("   4. Firewall bloqueando porta 587")
        print()
        print("Solução:")
        print("   1. Acessar: https://myaccount.google.com/apppasswords")
        print("   2. Gerar nova senha de app")
        print("   3. Atualizar EMAIL_HOST_PASSWORD no .env")
        print("   4. Executar este teste novamente")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print("⚠️  Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
