"""Testes do EmailService"""
from django.test import TestCase
from django.core import mail
from core.services.email_service import EmailService
from core.models import Comanda, Locacao, Locatario, Imovel, Locador, Usuario, LogNotificacao
from datetime import date, timedelta
from decimal import Decimal


class EmailServiceTest(TestCase):
    
    def setUp(self):
        """Criar dados de teste"""
        # Usuario
        usuario = Usuario.objects.create(username='test_user', email='test@test.com')
        
        # Locador
        locador = Locador.objects.create(
            usuario=usuario,
            nome_razao_social='Locador Teste',
            tipo_locador='PF',
            cpf_cnpj='12345678900',
            is_active=True
        )
        
        # Locatario
        self.locatario = Locatario.objects.create(
            nome_razao_social='Locatário Teste',
            cpf_cnpj='98765432100',
            email='locatario@test.com',
            telefone='41999999999',
            is_active=True
        )
        
        # Imovel
        imovel = Imovel.objects.create(
            locador=locador,
            codigo_imovel='TEST001',
            tipo_imovel='APARTAMENTO',
            endereco='Rua Teste',
            numero='123',
            bairro='Centro',
            cidade='Curitiba',
            estado='PR',
            cep='80000-000',
            area_total=Decimal('100.00'),  # CAMPO OBRIGATÓRIO
            valor_aluguel=Decimal('1000.00'),
            valor_condominio=Decimal('200.00'),
            is_active=True
        )
        
        # Locacao
        locacao = Locacao.objects.create(
            imovel=imovel,
            locatario=self.locatario,
            numero_contrato='TEST-001',
            status='ATIVO',
            data_inicio=date.today() - timedelta(days=30),
            data_fim=date.today() + timedelta(days=335),
            dia_vencimento=10,
            valor_aluguel=Decimal('1000.00'),
            is_active=True
        )
        
        # Comanda
        self.comanda = Comanda.objects.create(
            locacao=locacao,
            numero_comanda='TEST-202510-001',
            mes_referencia=date.today().replace(day=1),
            ano_referencia=date.today().year,
            data_vencimento=date.today() + timedelta(days=7),
            valor_iptu=Decimal('50.00'),
            status='PENDING',
            is_active=True
        )
    
    def test_envio_email_sucesso(self):
        """Testa envio de email com sucesso"""
        resultado = EmailService.enviar_notificacao(self.comanda, '7D')
        
        self.assertTrue(resultado)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('7 dias', mail.outbox[0].subject)
        
        # Verificar log criado
        log = LogNotificacao.objects.filter(comanda=self.comanda).first()
        self.assertIsNotNone(log)
        self.assertTrue(log.sucesso)
    
    def test_contexto_email(self):
        """Testa preparação de contexto"""
        contexto = EmailService.preparar_contexto(self.comanda, '7D')
        
        self.assertEqual(contexto['locatario_nome'], 'Locatário Teste')
        self.assertIn('Rua Teste', contexto['imovel_endereco'])
        self.assertIn('1,000', contexto['valor_aluguel'])
    
    def test_sem_email_locatario(self):
        """Testa comportamento quando locatário não tem email"""
        self.locatario.email = ''
        self.locatario.save()
        
        resultado = EmailService.enviar_notificacao(self.comanda, '7D')
        
        self.assertFalse(resultado)
        self.assertEqual(len(mail.outbox), 0)
