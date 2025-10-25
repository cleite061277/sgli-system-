import uuid
import hashlib
from decimal import Decimal
from typing import Optional
from datetime import date, timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# ============================================================================
# VALIDATORS
# ============================================================================

def validate_cpf(value: str) -> None:
    """Validate Brazilian CPF format and algorithm."""
    cpf = ''.join(filter(str.isdigit, value))
    
    if len(cpf) != 11:
        raise ValidationError(_('CPF deve ter 11 dígitos.'))
    
    if cpf == cpf[0] * 11:
        raise ValidationError(_('CPF inválido.'))
    
    def calculate_digit(cpf_partial: str, weight: int) -> str:
        total = sum(int(digit) * (weight - i) for i, digit in enumerate(cpf_partial))
        remainder = total % 11
        return '0' if remainder < 2 else str(11 - remainder)
    
    first_digit = calculate_digit(cpf[:9], 10)
    second_digit = calculate_digit(cpf[:9] + first_digit, 11)
    
    if cpf[-2:] != first_digit + second_digit:
        raise ValidationError(_('CPF inválido.'))


def validate_cnpj(value: str) -> None:
    """Validate Brazilian CNPJ format and algorithm."""
    cnpj = ''.join(filter(str.isdigit, value))
    
    if len(cnpj) != 14:
        raise ValidationError(_('CNPJ deve ter 14 dígitos.'))
    
    if cnpj == cnpj[0] * 14:
        raise ValidationError(_('CNPJ inválido.'))
    
    def calculate_digit(cnpj_partial: str, weights: list) -> str:
        total = sum(int(digit) * weight for digit, weight in zip(cnpj_partial, weights))
        remainder = total % 11
        return '0' if remainder < 2 else str(11 - remainder)
    
    first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    first_digit = calculate_digit(cnpj[:12], first_weights)
    second_digit = calculate_digit(cnpj[:12] + first_digit, second_weights)
    
    if cnpj[-2:] != first_digit + second_digit:
        raise ValidationError(_('CNPJ inválido.'))


def validate_cep(value: str) -> None:
    """Validate Brazilian CEP format."""
    import re
    if not re.match(r'^\d{5}-?\d{3}$', value):
        raise ValidationError(_('CEP deve estar no formato 12345-678 ou 12345678.'))


# ============================================================================
# BASE MODEL
# ============================================================================

class BaseModel(models.Model):
    """Abstract base model with common fields."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Identificador único do registro')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação'),
        help_text=_('Data e hora da criação do registro')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Data de Atualização'),
        help_text=_('Data e hora da última atualização do registro')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Ativo'),
        help_text=_('Indica se o registro está ativo (soft delete)')
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


# ============================================================================
# USER MODEL
# ============================================================================

class Usuario(AbstractUser, BaseModel):
    """Custom user model extending Django's AbstractUser."""
    
    class TipoUsuario(models.TextChoices):
        ADMINISTRADOR = 'ADMIN', _('Administrador')
        GERENTE = 'MANAGER', _('Gerente')
        ATENDENTE = 'ATTENDANT', _('Atendente')
        FINANCEIRO = 'FINANCIAL', _('Financeiro')
        LOCADOR = 'LANDLORD', _('Locador')
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TipoUsuario.choices,
        default=TipoUsuario.ATENDENTE,
        verbose_name=_('Tipo de Usuário'),
        help_text=_('Nível de permissão do usuário no sistema')
    )
    
    telefone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Telefone'),
        help_text=_('Telefone de contato')
    )
    
    cpf = models.CharField(
        max_length=14,
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('CPF'),
        help_text=_('CPF do usuário')
    )
    
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name=_('Avatar'),
        help_text=_('Foto de perfil do usuário')
    )
    
    def __str__(self) -> str:
        return f"{self.get_full_name() or self.username} ({self.get_tipo_usuario_display()})"
    
    class Meta:
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')
        db_table = 'core_usuario'


# ============================================================================
# LOCADOR MODEL
# ============================================================================

class Locador(BaseModel):
    """Property owner/landlord model."""
    
    class TipoLocador(models.TextChoices):
        PESSOA_FISICA = 'PF', _('Pessoa Física')
        PESSOA_JURIDICA = 'PJ', _('Pessoa Jurídica')
    
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.PROTECT,
        related_name='locador_profile',
        verbose_name=_('Usuário'),
        help_text=_('Usuário associado ao locador')
    )
    
    tipo_locador = models.CharField(
        max_length=2,
        choices=TipoLocador.choices,
        default=TipoLocador.PESSOA_FISICA,
        verbose_name=_('Tipo de Locador'),
        help_text=_('Pessoa física ou jurídica')
    )
    
    nome_razao_social = models.CharField(
        max_length=200,
        verbose_name=_('Nome/Razão Social'),
        help_text=_('Nome completo ou razão social')
    )
    
    cpf_cnpj = models.CharField(
        max_length=18,
        unique=True,
        verbose_name=_('CPF/CNPJ'),
        help_text=_('CPF para pessoa física ou CNPJ para pessoa jurídica')
    )
    
    telefone = models.CharField(
        max_length=20,
        verbose_name=_('Telefone'),
        help_text=_('Telefone principal de contato')
    )
    
    email = models.EmailField(
        verbose_name=_('E-mail'),
        help_text=_('E-mail principal de contato')
    )
    
    endereco_completo = models.TextField(
        verbose_name=_('Endereço Completo'),
        help_text=_('Endereço completo do locador')
    )
    
    cep = models.CharField(
        max_length=9,
        verbose_name=_('CEP'),
        help_text=_('CEP no formato 12345-678')
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name=_('Observações'),
        help_text=_('Observações gerais sobre o locador')
    )
    
    def __str__(self) -> str:
        return f"{self.nome_razao_social} ({self.cpf_cnpj})"
    
    class Meta:
        verbose_name = _('Locador')
        verbose_name_plural = _('Locadores')
        db_table = 'core_locador'


# ============================================================================
# IMOVEL MODEL
# ============================================================================

class Imovel(BaseModel):
    """Property model."""
    
    class StatusImovel(models.TextChoices):
        DISPONIVEL = 'AVAILABLE', _('Disponível')
        OCUPADO = 'OCCUPIED', _('Ocupado')
        MANUTENCAO = 'MAINTENANCE', _('Em Manutenção')
        VENDIDO = 'SOLD', _('Vendido')
        INATIVO = 'INACTIVE', _('Inativo')
    
    class TipoImovel(models.TextChoices):
        APARTAMENTO = 'APARTMENT', _('Apartamento')
        CASA = 'HOUSE', _('Casa')
        COMERCIAL = 'COMMERCIAL', _('Comercial')
        TERRENO = 'LAND', _('Terreno')
        GALPAO = 'WAREHOUSE', _('Galpão')
        SALA = 'OFFICE', _('Sala')
        LOJA = 'STORE', _('Loja')
    
    locador = models.ForeignKey(
        Locador,
        on_delete=models.PROTECT,
        related_name='imoveis',
        verbose_name=_('Locador'),
        help_text=_('Proprietário do imóvel')
    )
    
    codigo_imovel = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Código do Imóvel'),
        help_text=_('Código único de identificação do imóvel')
    )
    
    tipo_imovel = models.CharField(
        max_length=20,
        choices=TipoImovel.choices,
        verbose_name=_('Tipo do Imóvel'),
        help_text=_('Categoria do imóvel')
    )
    
    status = models.CharField(
        max_length=20,
        choices=StatusImovel.choices,
        default=StatusImovel.DISPONIVEL,
        verbose_name=_('Status'),
        help_text=_('Status atual do imóvel')
    )
    
    endereco = models.CharField(
        max_length=300,
        verbose_name=_('Endereço'),
        help_text=_('Logradouro completo')
    )
    
    numero = models.CharField(
        max_length=10,
        verbose_name=_('Número'),
        help_text=_('Número do imóvel')
    )
    
    bairro = models.CharField(
        max_length=100,
        verbose_name=_('Bairro'),
        help_text=_('Bairro do imóvel')
    )
    
    cidade = models.CharField(
        max_length=100,
        verbose_name=_('Cidade'),
        help_text=_('Cidade do imóvel')
    )
    
    estado = models.CharField(
        max_length=2,
        verbose_name=_('Estado'),
        help_text=_('UF do estado (2 letras)')
    )
    
    cep = models.CharField(
        max_length=9,
        verbose_name=_('CEP'),
        help_text=_('CEP no formato 12345-678')
    )
    
    area_total = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Área Total (m²)'),
        help_text=_('Área total do imóvel em metros quadrados')
    )
    
    quartos = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Quartos'),
        help_text=_('Número de quartos')
    )
    
    banheiros = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Banheiros'),
        help_text=_('Número de banheiros')
    )
    
    valor_aluguel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Valor do Aluguel'),
        help_text=_('Valor mensal do aluguel')
    )
    
    valor_condominio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Valor do Condomínio'),
        help_text=_('Valor mensal do condomínio')
    )
    
    descricao = models.TextField(
        blank=True,
        verbose_name=_('Descrição'),
        help_text=_('Descrição detalhada do imóvel')
    )
    
    @property
    def endereco_completo(self) -> str:
        return f"{self.endereco}, {self.numero} - {self.bairro}, {self.cidade}/{self.estado}"
    
    @property
    def valor_total_mensal(self) -> Decimal:
        return self.valor_aluguel + self.valor_condominio
    
    def __str__(self) -> str:
        return f"{self.codigo_imovel} - {self.endereco}, {self.numero}"
    
    class Meta:
        verbose_name = _('Imóvel')
        verbose_name_plural = _('Imóveis')
        db_table = 'core_imovel'


# ============================================================================
# LOCATARIO MODEL
# ============================================================================

class Locatario(BaseModel):
    """Tenant model."""
    
    nome_razao_social = models.CharField(
        max_length=200,
        verbose_name=_('Nome/Razão Social'),
        help_text=_('Nome completo ou razão social')
    )
    
    cpf_cnpj = models.CharField(
        max_length=18,
        unique=True,
        verbose_name=_('CPF/CNPJ'),
        help_text=_('CPF para pessoa física ou CNPJ para pessoa jurídica')
    )
    
    telefone = models.CharField(
        max_length=20,
        verbose_name=_('Telefone'),
        help_text=_('Telefone principal de contato')
    )
    
    email = models.EmailField(
        verbose_name=_('E-mail'),
        help_text=_('E-mail principal de contato')
    )
    
    endereco_completo = models.TextField(
        verbose_name=_('Endereço Completo'),
        help_text=_('Endereço completo do locatário')
    )
    
    renda_mensal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Renda Mensal'),
        help_text=_('Renda mensal declarada')
    )
    
    def __str__(self) -> str:
        return f"{self.nome_razao_social} ({self.cpf_cnpj})"
    
    class Meta:
        verbose_name = _('Locatário')
        verbose_name_plural = _('Locatários')
        db_table = 'core_locatario'


# ============================================================================
# LOCACAO MODEL
# ============================================================================

class Locacao(BaseModel):
    """Lease/rental agreement model."""
    
    class StatusLocacao(models.TextChoices):
        ATIVA = 'ACTIVE', _('Ativa')
        INATIVA = 'INACTIVE', _('Inativa')
        PENDENTE = 'PENDING', _('Pendente')
        VENCIDA = 'EXPIRED', _('Vencida')
    
    imovel = models.ForeignKey(
        Imovel,
        on_delete=models.PROTECT,
        related_name='locacoes',
        verbose_name=_('Imóvel'),
        help_text=_('Imóvel objeto da locação')
    )
    
    locatario = models.ForeignKey(
        Locatario,
        on_delete=models.PROTECT,
        related_name='locacoes',
        verbose_name=_('Locatário'),
        help_text=_('Locatário responsável pelo contrato')
    )
    
    numero_contrato = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Número do Contrato'),
        help_text=_('Número único do contrato de locação')
    )
    
    status = models.CharField(
        max_length=20,
        choices=StatusLocacao.choices,
        default=StatusLocacao.PENDENTE,
        verbose_name=_('Status'),
        help_text=_('Status atual do contrato')
    )
    
    data_inicio = models.DateField(
        verbose_name=_('Data de Início'),
        help_text=_('Data de início da locação')
    )
    
    data_fim = models.DateField(
        verbose_name=_('Data de Fim'),
        help_text=_('Data de término da locação')
    )
    
    valor_aluguel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Valor do Aluguel'),
        help_text=_('Valor mensal do aluguel no contrato')
    )
    
    def __str__(self) -> str:
        return f"Contrato {self.numero_contrato} - {self.locatario.nome_razao_social}"
    
    class Meta:
        verbose_name = _('Locação')
        verbose_name_plural = _('Locações')
        db_table = 'core_locacao'
# ============================================================================
# COMANDA MODEL (Sistema Financeiro)
# ============================================================================

class Comanda(BaseModel):
    """Invoice/billing model for monthly rent payments."""
    
    class StatusComanda(models.TextChoices):
        PENDENTE = 'PENDING', _('Pendente')
        PAGA = 'PAID', _('Paga')
        VENCIDA = 'OVERDUE', _('Vencida')
        PARCIALMENTE_PAGA = 'PARTIAL', _('Parcialmente Paga')
        CANCELADA = 'CANCELLED', _('Cancelada')
    
    locacao = models.ForeignKey(
        Locacao,
        on_delete=models.PROTECT,
        related_name='comandas',
        verbose_name=_('Locação'),
        help_text=_('Contrato de locação associado')
    )
    
    numero_comanda = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Número da Comanda'),
        help_text=_('Número único da comanda')
    )
    
    mes_referencia = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name=_('Mês de Referência'),
        help_text=_('Mês de referência da cobrança (1-12)')
    )
    
    ano_referencia = models.PositiveIntegerField(
        validators=[MinValueValidator(2020), MaxValueValidator(2050)],
        verbose_name=_('Ano de Referência'),
        help_text=_('Ano de referência da cobrança')
    )
    
    status = models.CharField(
        max_length=20,
        choices=StatusComanda.choices,
        default=StatusComanda.PENDENTE,
        verbose_name=_('Status'),
        help_text=_('Status atual da comanda')
    )
    
    data_vencimento = models.DateField(
        verbose_name=_('Data de Vencimento'),
        help_text=_('Data de vencimento da comanda')
    )
    
    # Valores da cobrança
    valor_aluguel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Valor do Aluguel'),
        help_text=_('Valor do aluguel no mês de referência')
    )
    
    valor_condominio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Valor do Condomínio'),
        help_text=_('Valor do condomínio no mês de referência')
    )
    
    valor_iptu = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Valor do IPTU'),
        help_text=_('Valor proporcional do IPTU no mês')
    )
    
    # Taxas e outros valores
    valor_administracao = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Taxa de Administração'),
        help_text=_('Taxa de administração da imobiliária')
    )
    
    outros_creditos = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Outros Créditos'),
        help_text=_('Créditos diversos (valores negativos reduzem o total)')
    )
    
    outros_debitos = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Outros Débitos'),
        help_text=_('Débitos diversos (multas, juros, etc.)')
    )
    
    multa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Multa'),
        help_text=_('Multa por atraso no pagamento')
    )
    
    juros = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Juros'),
        help_text=_('Juros por atraso no pagamento')
    )
    
    desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Desconto'),
        help_text=_('Desconto aplicado na comanda')
    )
    
    # Controle de pagamento
    data_pagamento = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data de Pagamento'),
        help_text=_('Data efetiva do pagamento')
    )
    
    valor_pago = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Valor Pago'),
        help_text=_('Valor efetivamente pago')
    )
    
    forma_pagamento = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Forma de Pagamento'),
        help_text=_('Forma de pagamento utilizada')
    )
    
    comprovante_pagamento = models.FileField(
        upload_to='comprovantes/',
        blank=True,
        null=True,
        verbose_name=_('Comprovante de Pagamento'),
        help_text=_('Arquivo do comprovante de pagamento')
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name=_('Observações'),
        help_text=_('Observações sobre a comanda')
    )
    
    @property
    def valor_total(self) -> Decimal:
        """Calculate total invoice amount."""
        total = (
            self.valor_aluguel + 
            self.valor_condominio + 
            self.valor_iptu + 
            self.valor_administracao + 
            self.outros_debitos + 
            self.multa + 
            self.juros + 
            self.outros_creditos  # Can be negative
        ) - self.desconto
        
        return max(total, Decimal('0.00'))
    
    @property
    def valor_pendente(self) -> Decimal:
        """Calculate pending amount."""
        return max(self.valor_total - self.valor_pago, Decimal('0.00'))
    
    @property
    def is_vencida(self) -> bool:
        """Check if invoice is overdue."""
        return (
            timezone.now().date() > self.data_vencimento and 
            self.status not in [self.StatusComanda.PAGA, self.StatusComanda.CANCELADA]
        )
    
    @property
    def dias_atraso(self) -> int:
        """Calculate days overdue."""
        if not self.is_vencida:
            return 0
        return (timezone.now().date() - self.data_vencimento).days
    
    def calcular_multa_juros(self, data_referencia: date = None) -> dict:
        """
        Calculate late fees and interest based on overdue days.
        
        Business rules:
        - Multa: 2% do valor do aluguel após 1 dia de atraso
        - Juros: 1% ao mês (pro-rata) sobre o valor total
        """
        if data_referencia is None:
            data_referencia = timezone.now().date()
        
        # Only calculate if overdue
        if data_referencia <= self.data_vencimento:
            return {'multa': Decimal('0.00'), 'juros': Decimal('0.00')}
        
        dias_atraso = (data_referencia - self.data_vencimento).days
        
        # Calculate late fee (2% of rent after 1 day)
        multa = self.valor_aluguel * Decimal('0.02') if dias_atraso >= 1 else Decimal('0.00')
        
        # Calculate interest (1% per month, pro-rata daily)
        juros_mensal = Decimal('0.01')  # 1% per month
        juros_diario = juros_mensal / 30  # Approximate daily rate
        juros = self.valor_aluguel * juros_diario * dias_atraso
        
        return {
            'multa': multa.quantize(Decimal('0.01')),
            'juros': juros.quantize(Decimal('0.01'))
        }
    
    def aplicar_multa_juros(self, salvar: bool = True) -> None:
        """Apply calculated late fees and interest to the invoice."""
        if not self.is_vencida:
            return
        
        valores = self.calcular_multa_juros()
        self.multa = valores['multa']
        self.juros = valores['juros']
        
        if salvar:
            self.save(update_fields=['multa', 'juros', 'updated_at'])
    
    def clean(self) -> None:
        """Validate model data."""
        super().clean()
        
        if self.valor_pago > self.valor_total:
            if abs(self.valor_pago - self.valor_total) > Decimal('0.01'):  # Allow small rounding differences
                raise ValidationError(_('Valor pago não pode ser maior que o valor total.'))
    
    def save(self, *args, **kwargs) -> None:
        """Override save to update status based on payment."""
        # Auto-update status based on payment
        if self.valor_pago >= self.valor_total and self.valor_total > 0:
            self.status = self.StatusComanda.PAGA
        elif self.valor_pago > 0:
            self.status = self.StatusComanda.PARCIALMENTE_PAGA
        elif self.is_vencida:
            self.status = self.StatusComanda.VENCIDA
        else:
            self.status = self.StatusComanda.PENDENTE
        
        # Generate automatic number if not provided
        if not self.numero_comanda:
            self.numero_comanda = self._gerar_numero_automatico()
            
        super().save(*args, **kwargs)
    
    def _gerar_numero_automatico(self) -> str:
        """Generate automatic invoice number in YYYYMM-XXXX format."""
        prefix = f"{self.ano_referencia}{self.mes_referencia:02d}"
        
        # Find the last invoice for this month/year
        last_comanda = (Comanda.objects
                       .filter(numero_comanda__startswith=prefix)
                       .order_by('-numero_comanda')
                       .first())
        
        if last_comanda:
            try:
                last_seq = int(last_comanda.numero_comanda.split('-')[1])
                new_seq = last_seq + 1
            except (IndexError, ValueError):
                new_seq = 1
        else:
            new_seq = 1
        
        return f"{prefix}-{new_seq:04d}"
    
    def __str__(self) -> str:
        return f"Comanda {self.numero_comanda} - {self.mes_referencia:02d}/{self.ano_referencia}"
    
    class Meta:
        verbose_name = _('Comanda')
        verbose_name_plural = _('Comandas')
        db_table = 'core_comanda'
        unique_together = ['locacao', 'mes_referencia', 'ano_referencia']
        ordering = ['-ano_referencia', '-mes_referencia']
