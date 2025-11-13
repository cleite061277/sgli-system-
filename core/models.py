import uuid
import hashlib
from decimal import Decimal
from typing import Optional
from datetime import date, timedelta

from django.db import models, transaction, IntegrityError
from django.db.models import F
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
    
    representante = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Representante'),
        help_text=_('Nome do representante legal do locador')
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

# NOVOS CAMPOS: Utilidades
    conta_agua_esgoto = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Conta de Água/Esgoto'),
        help_text=_('Exemplo: 50683-4')
    )
    
    numero_hidrometro = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Número do Hidrômetro'),
        help_text=_('Exemplo: Y19S381570')
    )
    
    unidade_consumidora_energia = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Unidade Consumidora de Energia'),
        help_text=_('Exemplo: 84829729')
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

# ===========================================================================
# MODELO FIADOR (NOVO - Adicionar ANTES do modelo Locatario)
# ===========================================================================

class Fiador(BaseModel):
    """Fiador/Garantidor do locatário."""
    
    # Dados Pessoais
    nome_completo = models.CharField(
        max_length=200,
        verbose_name=_('Nome Completo'),
        help_text=_('Nome completo do fiador')
    )
    
    cpf = models.CharField(
        max_length=14,
        unique=True,
        validators=[validate_cpf],
        verbose_name=_('CPF'),
        help_text=_('CPF do fiador (formato: 000.000.000-00)')
    )
    
    rg = models.CharField(
        max_length=50,
        verbose_name=_('RG'),
        help_text=_('Exemplo: 109521205 SESP PR')
    )
    
    data_nascimento = models.DateField(
        verbose_name=_('Data de Nascimento'),
        help_text=_('Data de nascimento do fiador')
    )
    
    # Filiação
    nome_pai = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Nome do Pai'),
        help_text=_('Nome completo do pai')
    )
    
    nome_mae = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Nome da Mãe'),
        help_text=_('Nome completo da mãe')
    )
    
    # Contatos
    telefone = models.CharField(
        max_length=20,
        verbose_name=_('Telefone Principal'),
        help_text=_('Telefone principal de contato')
    )
    
    email = models.EmailField(
        verbose_name=_('E-mail'),
        help_text=_('E-mail principal de contato')
    )
    
    outro_telefone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Outro Telefone'),
        help_text=_('Telefone secundário')
    )
    
    nome_contato_emergencia = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Nome do Contato de Emergência'),
        help_text=_('Nome completo do contato')
    )
    
    telefone_contato_emergencia = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Telefone do Contato de Emergência'),
        help_text=_('Telefone do contato')
    )
    
    # Endereço
    endereco_completo = models.TextField(
        verbose_name=_('Endereço Completo'),
        help_text=_('Endereço completo do fiador')
    )
    
    cep = models.CharField(
        max_length=9,
        verbose_name=_('CEP'),
        help_text=_('CEP no formato 12345-678')
    )
    
    # Dados Profissionais
    empresa_trabalho = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Empresa/Trabalho'),
        help_text=_('Nome da empresa onde trabalha')
    )
    
    endereco_empresa = models.TextField(
        blank=True,
        verbose_name=_('Endereço da Empresa'),
        help_text=_('Endereço completo da empresa')
    )
    
    telefone_empresa = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Telefone da Empresa'),
        help_text=_('Telefone da empresa')
    )
    
    contato_empresa = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Contato na Empresa'),
        help_text=_('Nome do contato/supervisor na empresa')
    )
    
    tempo_empresa = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Tempo na Empresa'),
        help_text=_('Exemplo: 2 anos e 3 meses')
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
        return f"{self.nome_completo} (CPF: {self.cpf})"
    
    class Meta:
        verbose_name = _('Fiador')
        verbose_name_plural = _('Fiadores')
        db_table = 'core_fiador'
        ordering = ['nome_completo']

# ============================================================================
# LOCATARIO MODEL
# ============================================================================

class Locatario(BaseModel):
    """Tenant model - ATUALIZADO com novos campos."""
    
    # Dados Pessoais Básicos
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
    
    # NOVOS CAMPOS
    rg = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('RG'),
        help_text=_('Exemplo: 109521205 SESP PR')
    )
    
    data_nascimento = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data de Nascimento'),
        help_text=_('Data de nascimento do locatário')
    )
    
    # Filiação
    nome_pai = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Nome do Pai'),
        help_text=_('Nome completo do pai')
    )
    
    nome_mae = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Nome da Mãe'),
        help_text=_('Nome completo da mãe')
    )
    
    # Contatos
    telefone = models.CharField(
        max_length=20,
        verbose_name=_('Telefone'),
        help_text=_('Telefone principal de contato')
    )
    
    email = models.EmailField(
        verbose_name=_('E-mail'),
        help_text=_('E-mail principal de contato')
    )
    
    # NOVO: Outros Contatos
    outro_telefone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Outro Telefone'),
        help_text=_('Telefone secundário')
    )
    
    nome_contato_emergencia = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Nome do Contato de Emergência'),
        help_text=_('Nome completo do contato')
    )
    
    telefone_contato_emergencia = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Telefone do Contato de Emergência'),
        help_text=_('Telefone do contato')
    )
    
    # Endereço
    endereco_completo = models.TextField(
        verbose_name=_('Endereço Completo'),
        help_text=_('Endereço completo do locatário')
    )
    
    # NOVOS CAMPOS: Dados Profissionais
    empresa_trabalho = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Empresa/Trabalho'),
        help_text=_('Nome da empresa onde trabalha')
    )
    
    endereco_empresa = models.TextField(
        blank=True,
        verbose_name=_('Endereço da Empresa'),
        help_text=_('Endereço completo da empresa')
    )
    
    telefone_empresa = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Telefone da Empresa'),
        help_text=_('Telefone da empresa')
    )
    
    contato_empresa = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Contato na Empresa'),
        help_text=_('Nome do contato/supervisor na empresa')
    )
    
    tempo_empresa = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Tempo na Empresa'),
        help_text=_('Exemplo: 2 anos e 3 meses')
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
    
    # NOVO: Relacionamento com Fiador
    fiador = models.ForeignKey(
        Fiador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locatarios_afiancados',
        verbose_name=_('Fiador'),
        help_text=_('Fiador/Garantidor do locatário (se houver)')
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
    
    def save(self, *args, **kwargs):
        """Gera numero_contrato sequencial único se não existir."""
        if not self.numero_contrato:
            from django.utils import timezone
            import re
            
            hoje = timezone.now()
            ano_mes = f"{hoje.year}{hoje.month:02d}"
            
            # Extrair últimos 6 dígitos do CPF/CNPJ do locatário
            cpf_cnpj = re.sub(r'\D', '', self.locatario.cpf_cnpj)  # Remove não-dígitos
            cpf_6dig = cpf_cnpj[-6:] if len(cpf_cnpj) >= 6 else cpf_cnpj.zfill(6)
            
            # Pegar primeiros 4 caracteres do código do imóvel
            codigo_imovel = self.imovel.codigo_imovel[:5].upper() if self.imovel.codigo_imovel else "XXXX"
            
            # Formato: YYYYMM-XXXXXX-XXXX (ex: 202511123456-A101)
            numero_base = f"{ano_mes}{cpf_6dig}{codigo_imovel}"
            
            # Verificar se já existe (caso improvável de colisão)
            numero_final = numero_base
            contador = 1
            while Locacao.objects.filter(numero_contrato=numero_final).exists():
                numero_final = f"{numero_base}-{contador}"
                contador += 1
            
            self.numero_contrato = numero_final
        
        super().save(*args, **kwargs)
    
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
        blank=True,  # Permitir vazio para geração automática
        verbose_name=_('Número do Contrato'),
        help_text=_('Gerado automaticamente: YYYYMM + 6 dígitos CPF + código imóvel')
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
    
    dia_vencimento = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name=_('Dia de Vencimento'),
        help_text=_('Dia do mês para vencimento da comanda (1-31)')
    )
    
    def __str__(self) -> str:
        return f"Contrato {self.numero_contrato} - {self.locatario.nome_razao_social}"
    
    @classmethod
    def get_contratos_ativos_count(cls):
        """Retorna contagem de contratos ativos."""
        return cls.objects.filter(status=cls.StatusLocacao.ATIVA).count()
    
    @classmethod
    def get_contratos_vencendo(cls, dias=60):
        """Retorna contratos que vencem em X dias."""
        from django.utils import timezone
        from datetime import timedelta
        
        data_limite = timezone.now().date() + timedelta(days=dias)
        return cls.objects.filter(
            status=cls.StatusLocacao.ATIVA,
            data_fim__lte=data_limite,
            data_fim__gte=timezone.now().date()
        ).count()
    
    class Meta:
        verbose_name = _('Locação')
        verbose_name_plural = _('Locações')
        db_table = 'core_locacao'


# ============================================================================
# PAGAMENTO CHOICES (Global - usadas por Comanda e Pagamento)
# ============================================================================

class FormaPagamento(models.TextChoices):
    """Formas de pagamento disponíveis no sistema"""
    DINHEIRO = 'dinheiro', _('Dinheiro')
    PIX = 'pix', _('PIX')
    TRANSFERENCIA = 'transferencia', _('Transferência Bancária')
    BOLETO = 'boleto', _('Boleto')
    CARTAO_CREDITO = 'cartao_credito', _('Cartão de Crédito')
    CARTAO_DEBITO = 'cartao_debito', _('Cartão de Débito')
    CHEQUE = 'cheque', _('Cheque')

class StatusPagamento(models.TextChoices):
    """Status de pagamento"""
    PENDENTE = 'pendente', _('Pendente')
    CONFIRMADO = 'confirmado', _('Confirmado')
    CANCELADO = 'cancelado', _('Cancelado')
    ESTORNADO = 'estornado', _('Estornado')


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
    
    mes_referencia = models.DateField(
        verbose_name=_('Mês de Referência'),
        help_text=_('Primeiro dia do mês de referência (formato YYYY-MM-01)')
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
    	default=Decimal('0.00'),  # ← ADICIONAR
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
    
    valor_multa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Multa'),
        help_text=_('Multa por atraso no pagamento')
    )
    
    valor_juros = models.DecimalField(
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
        max_length=20,
        blank=True,
        choices=FormaPagamento.choices,
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
    
    # Controle de notificações
    notificacao_enviada_7dias = models.BooleanField(
        default=False,
        verbose_name='Notificação 7 dias enviada'
    )
    
    notificacao_enviada_1dia = models.BooleanField(
        default=False,
        verbose_name='Notificação 1 dia enviada'
    )
    
    notificacao_atraso_enviada = models.BooleanField(
        default=False,
        verbose_name='Notificação de atraso enviada'
    )
    
    notificacao_enviada_10dias = models.BooleanField(
        default=False,
        verbose_name='Notificação 10 dias enviada'
    )
    
    notificacao_enviada_vencimento = models.BooleanField(
        default=False,
        verbose_name='Notificação dia vencimento enviada'
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name=_('Observações'),
        help_text=_('Observações sobre a comanda')
    )
    
    @property
    def valor_total(self) -> Decimal:
        """Calculate total invoice amount."""
        valor_aluguel = self.valor_aluguel or Decimal("0.00")
        valor_condominio = self.valor_condominio or Decimal("0.00")
        valor_iptu = self.valor_iptu or Decimal("0.00")
        valor_administracao = self.valor_administracao or Decimal("0.00")
        outros_creditos = self.outros_creditos or Decimal("0.00")
        outros_debitos = self.outros_debitos or Decimal("0.00")
        multa = self.valor_multa or Decimal("0.00")
        juros = self.valor_juros or Decimal("0.00")
        desconto = self.desconto or Decimal("0.00")
        
        total = (
            valor_aluguel + 
            valor_condominio + 
            valor_iptu + 
            valor_administracao + 
            outros_debitos + 
            multa + 
            juros
        ) - outros_creditos - desconto  # ✅ CORRIGIDO: outros_creditos SUBTRAI
        
        return max(total, Decimal("0.00"))
        
    @property
    def valor_pendente(self) -> Decimal:
        """Calculate pending amount."""
        # Calcular total pago confirmado
        total_pago = self.pagamentos.filter(
            status='confirmado'
        ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
        
        # Pendente = Valor total - Total pago
        pendente = self.valor_total - total_pago
        
        return max(pendente, Decimal('0.00'))
    
    def get_saldo(self):
        """
        Calcula saldo: Total pago - Valor da comanda
        Positivo = a favor do cliente (pagou a mais)
        Negativo = a favor do locatário (deve)
        """
        total_pago = self.pagamentos.filter(
            status="confirmado"
        ).aggregate(
            total=models.Sum('valor_pago')
        )['total'] or Decimal('0.00')
        
        # Saldo = Total pago - Valor da comanda
        # Usa valor_total que já calcula corretamente
        # Positivo = cliente pagou a mais (tem crédito)
        # Negativo = cliente deve (débito)
        saldo = total_pago - self.valor_total
        return saldo
        
          
    def get_saldo_formatado(self):
        """Retorna saldo formatado em R$ com sinal"""
        saldo = self.get_saldo()
        if saldo == 0:
            return "R$ 0,00"
        elif saldo > 0:
            return f"+R$ {saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        else:
            return f"-R$ {abs(saldo):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def is_vencida(self) -> bool:
        """Check if invoice is overdue."""

        # 🎯 CORREÇÃO DE BUG (Null Check):
        if self.data_vencimento is None:
            return False

        return (
            timezone.now().date() > self.data_vencimento and 
            self.status not in [self.StatusComanda.PAGA, self.StatusComanda.CANCELADA]
    )
    
    @property
    def dias_atraso(self) -> int:
        """Calculate days overdue."""

        # 🎯 CORREÇÃO DE BUG (Null Check):
        if not self.data_vencimento or not self.is_vencida:
            return 0
        # O cálculo deve ocorrer APENAS se a comanda estiver vencida E tiver data_vencimento
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
        
        # Calculate late fee (10% of rent after 1 day)
        multa = self.valor_aluguel * Decimal('0.10') if dias_atraso >= 1 else Decimal('0.00')
        
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
        self.valor_multa = valores['multa']
        self.valor_juros = valores['juros']
        
        if salvar:
            self.save(update_fields=['valor_multa', 'valor_juros', 'updated_at'])
    
    def clean(self) -> None:
        """Validate model data."""
        super().clean()
        
        if self.valor_pago > self.valor_total:
            if abs(self.valor_pago - self.valor_total) > Decimal('0.01'):  # Allow small rounding differences
                raise ValidationError(_('Valor pago não pode ser maior que o valor total.'))
    
    def save(self, *args, **kwargs):
        """
        Save override para Comanda: gera numero_comanda no formato YYYYMM-XXXX.
        Usa retry atômico para evitar colisões UNIQUE.
        """
        from django.db import transaction, IntegrityError
        
        # Se não tiver numero_comanda, delega ao save padrão
        if not hasattr(self, 'numero_comanda'):
            return super(type(self), self).save(*args, **kwargs)
        
        # Se já existe numero_comanda (edição), salva normalmente
        if self.numero_comanda:
            return super().save(*args, **kwargs)
        
        # mes_referencia é DateField -> extrair ano e mês
        if hasattr(self, 'mes_referencia') and getattr(self.mes_referencia, 'month', None):
            when_year = int(self.mes_referencia.year)
            when_month = int(self.mes_referencia.month)
        else:
            # Fallback
            when_year = int(self.ano_referencia)
            when_month = int(self.mes_referencia)
        
        prefix = f"{when_year}{when_month:02d}"
        
        MAX_ATTEMPTS = 8
        last_exc = None
        
        for attempt in range(MAX_ATTEMPTS):
            try:
                with transaction.atomic():
                    last = (Comanda.objects
                           .filter(numero_comanda__startswith=prefix)
                           .order_by('-numero_comanda')
                           .first())
                    
                    if last and getattr(last, 'numero_comanda', None):
                        try:
                            last_seq = int(last.numero_comanda.split('-')[-1])
                            new_seq = last_seq + 1
                        except (IndexError, ValueError):
                            new_seq = 1
                    else:
                        new_seq = 1
                    
                    self.numero_comanda = f"{prefix}-{new_seq:04d}"
                    super().save(*args, **kwargs)
                
                return
                
            except IntegrityError as exc:
                last_exc = exc
                self.numero_comanda = None
                continue
        
        raise IntegrityError(
            f"Não foi possível gerar numero_comanda único após {MAX_ATTEMPTS} tentativas"
        ) from last_exc
    
    def __str__(self) -> str:
        return f"Comanda {self.numero_comanda} - {self.mes_referencia:02d}/{self.ano_referencia}"
    	
class Meta:
        verbose_name = _('Comanda')
        verbose_name_plural = _('Comandas')
        db_table = 'core_comanda'
        unique_together = ['locacao', 'mes_referencia', 'ano_referencia']
        ordering = ['-ano_referencia', '-mes_referencia']

# ============================================================================
# PAGAMENTO MODEL
# ============================================================================

class Pagamento(BaseModel):
    """
    Payment tracking model with complete audit trail.
    Tracks individual payments made against comandas.
    """
    FORMA_PAGAMENTO_CHOICES = (
        ('BO', _('Boleto')),
        ('PI', _('Pix')),
        ('TR', _('Transferência')),
        ('DE', _('Dinheiro')),
        ('CH', _('Cheque')),
        ('OU', _('Outro')),
    )
    
    # Relacionamentos
    comanda = models.ForeignKey(
        'Comanda',
        on_delete=models.CASCADE,
        related_name='pagamentos',
        verbose_name=_('Comanda')
    )
    
    usuario_registro = models.ForeignKey(
        'Usuario',
        on_delete=models.PROTECT,
        related_name='pagamentos_registrados',
        verbose_name=_('Usuário que Registrou')
    )
    
    # Identificação
    numero_pagamento = models.CharField(max_length=50,
        unique=True,
        editable=False,
        verbose_name=_('Número do Pagamento'))
    
    # Valores
    valor_pago = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Valor Pago')
    )
    
    # Datas
    data_pagamento = models.DateField(
        verbose_name=_('Data do Pagamento')
    )
    
    data_confirmacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Data de Confirmação')
    )
    
    # Forma e Status
    forma_pagamento = models.CharField(
        max_length=20,
        choices=FormaPagamento.choices,
        verbose_name=_('Forma de Pagamento')
    )
    
    status = models.CharField(
        max_length=20,
        choices=StatusPagamento.choices,
        default=StatusPagamento.PENDENTE,
        verbose_name=_('Status')
    )
    
    # Documentação
    comprovante = models.FileField(
        upload_to='comprovantes/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('Comprovante')
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name=_('Observações')
    )
    
    def _gerar_numero_automatico(self):
        """Generate sequential payment number."""
        from django.utils import timezone
        hoje = timezone.now()
        prefixo = f"PAG{hoje.year}{hoje.month:02d}"
        
        # Usar select_for_update para evitar race condition
        ultimo = Pagamento.objects.filter(
            numero_pagamento__startswith=prefixo
        ).select_for_update().order_by('-numero_pagamento').first()
        
        if ultimo:
            try:
                ultimo_numero = int(ultimo.numero_pagamento[-4:])
                novo_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                novo_numero = 1
        else:
            novo_numero = 1
        
        return f"{prefixo}{novo_numero:04d}"
    
    def _atualizar_comanda(self):
        """Update comanda's paid value based on confirmed payments."""
        total_pago = self.comanda.pagamentos.filter(
            status="confirmado"
        ).aggregate(
            total=models.Sum('valor_pago')
        )['total'] or Decimal('0.00')
        
        self.comanda.valor_pago = total_pago
        self.comanda.save(update_fields=['valor_pago'])
    
    def __str__(self):
        return f"{self.numero_pagamento} - {self.forma_pagamento} - R$ {self.valor_pago}"
    

    def save(self, *args, **kwargs):
        """Gera numero_pagamento sequencial único"""
        if not self.numero_pagamento:
            from django.utils import timezone
            hoje = timezone.now()
            prefix = f"PAG{hoje.year}{hoje.month:02d}"
            
            # Usar SequenceCounter para garantir unicidade
            seq = SequenceCounter.get_next(prefix)
            self.numero_pagamento = f"{prefix}-{seq:04d}"
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Pagamento')
        verbose_name_plural = _('Pagamentos')
        ordering = ['-data_pagamento', '-created_at']
        db_table = 'core_pagamento'


# Adicionar ao modelo Imovel (depois dos campos existentes)
# template_contrato = models.FileField(
#     upload_to='templates_contratos/',
#     blank=True,
#     null=True,
#     verbose_name=_('Template de Contrato Customizado')
# )


from django.core.exceptions import ValidationError

def validar_arquivo_template(arquivo):
    """Validar se o arquivo é .docx ou .odt"""
    import os
    ext = os.path.splitext(arquivo.name)[1].lower()
    if ext not in ['.docx', '.odt']:
        raise ValidationError('Apenas arquivos .docx ou .odt são permitidos')

# ============================================================================
# TEMPLATE CONTRATO MODEL
# ============================================================================

    ## AUTO-GENERATED NUMERO_PAGAMENTO - inserido em 2025-11-04T03:43:30.631563Z
    def _generate_numero(self):
        """Gera um identificador curto único baseado em UUID."""
        import uuid
        return uuid.uuid4().hex[:12].upper()
    
    def save(self, *args, **kwargs):
        """Garante numero_pagamento único antes de salvar."""
        if not getattr(self, 'numero_pagamento', None):
            for _ in range(10):
                candidate = self._generate_numero()
                if not type(self).objects.filter(numero_pagamento=candidate).exists():
                    self.numero_pagamento = candidate
                    break
            else:
                raise ValueError('Não foi possível gerar numero_pagamento único após várias tentativas.')
        return super(type(self), self).save(*args, **kwargs)

class TemplateContrato(BaseModel):
    """Template de contrato customizável."""
    
    nome = models.CharField(
        max_length=100,
        verbose_name=_('Nome do Template')
    )
    
    descricao = models.TextField(
        blank=True,
        verbose_name=_('Descrição')
    )
    
    arquivo_template = models.FileField(
        upload_to='templates_contratos/',
        validators=[validar_arquivo_template],
        verbose_name=_('Arquivo do Template'),
        help_text=_('Formatos aceitos: .docx (Word) ou .odt (LibreOffice)')
    )
    
    # Associações opcionais
    locador = models.ForeignKey(
        'Locador',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='templates_contrato',
        verbose_name=_('Locador Específico'),
        help_text=_('Se preenchido, este template será usado para este locador')
    )
    
    tipo_imovel = models.CharField(
        max_length=20,
        choices=Imovel.TipoImovel.choices,
        blank=True,
        verbose_name=_('Tipo de Imóvel'),
        help_text=_('Se preenchido, este template será usado para este tipo')
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name=_('Template Padrão'),
        help_text=_('Usar como template padrão quando não houver específico')
    )
    
    class Meta:
        verbose_name = _('Template de Contrato')
        verbose_name_plural = _('Templates de Contratos')
        ordering = ['-is_default', 'nome']
        db_table = 'core_template_contrato'
    
    def __str__(self):
        return f"{self.nome} ({'Padrão' if self.is_default else 'Customizado'})"



# ========== MODELO DE CONFIGURAÇÃO DO SISTEMA ==========
class ConfiguracaoSistema(models.Model):
    """Configurações gerais do sistema"""
    
    # Configurações de comandas
    dia_vencimento_padrao = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Dia do mês para vencimento das comandas (1-31)"
    )
    
    percentual_multa = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('2.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text="Percentual de multa por atraso (%)"
    )
    
    percentual_juros_mensal = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text="Percentual de juros ao mês (%)"
    )
    
    
    gerar_comandas_automaticamente = models.BooleanField(
        default=True,
        help_text="Gerar comandas automaticamente todo mês"
    )
    
    # Metadados
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='configuracoes_atualizadas'
    )
    
    class Meta:
        verbose_name = "Configuração do Sistema"
        verbose_name_plural = "Configurações do Sistema"
    
    def __str__(self):
        return f"Configurações (Vencimento: dia {self.dia_vencimento_padrao})"
    
    def get_config(cls):
        """Retorna a configuração única do sistema"""
        config, created = cls.objects.get_or_create(pk=1)
        return config


class LogGeracaoComandas(models.Model):
    """Histórico de execuções da geração automática de comandas"""
    
    data_execucao = models.DateTimeField(auto_now_add=True)
    mes_referencia = models.DateField(help_text="Mês/ano de referência (YYYY-MM-01)")
    
    comandas_geradas = models.IntegerField(default=0)
    comandas_duplicadas = models.IntegerField(default=0)
    locacoes_processadas = models.IntegerField(default=0)
    
    sucesso = models.BooleanField(default=True)
    mensagem = models.TextField(blank=True)
    erro = models.TextField(blank=True)
    
    executado_por = models.CharField(
        max_length=50,
        default='Sistema',
        help_text="manual, cron, celery, sistema"
    )
    
    class Meta:
        verbose_name = "Log de Geração de Comandas"
        verbose_name_plural = "Logs de Geração de Comandas"
        ordering = ['-data_execucao']
    
    def __str__(self):
        return f"Geração {self.mes_referencia.strftime('%m/%Y')} - {self.comandas_geradas} comandas"



class LogNotificacao(BaseModel):
    """Log de notificações enviadas"""
    
    class TipoNotificacao(models.TextChoices):
        LEMBRETE_10_DIAS = '10D', _('Lembrete 10 dias')
        LEMBRETE_7_DIAS = '7D', _('Lembrete 7 dias')
        LEMBRETE_1_DIA = '1D', _('Lembrete 1 dia')
        DIA_VENCIMENTO = 'VEN', _('Dia do vencimento')
        ATRASO_1_DIA = 'ATR1', _('Atraso 1 dia')
        ATRASO_7_DIAS = 'ATR7', _('Atraso 7 dias')
        ATRASO_14_DIAS = 'ATR14', _('Atraso 14 dias')
        ATRASO_21_DIAS = 'ATR21', _('Atraso 21 dias')
    
    comanda = models.ForeignKey(
        'Comanda',
        on_delete=models.CASCADE,
        related_name='logs_notificacao',
        verbose_name=_('Comanda')
    )
    
    tipo_notificacao = models.CharField(
        max_length=10,
        choices=TipoNotificacao.choices,
        verbose_name=_('Tipo de Notificação')
    )
    
    destinatario_email = models.EmailField(
        verbose_name=_('Email Destinatário')
    )
    
    enviado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Enviado em')
    )
    
    sucesso = models.BooleanField(
        default=True,
        verbose_name=_('Enviado com sucesso')
    )
    
    mensagem_erro = models.TextField(
        blank=True,
        verbose_name=_('Mensagem de erro')
    )
    
    def __str__(self):
        return f"{self.get_tipo_notificacao_display()} - {self.comanda.numero_comanda}"
    
    class Meta:
        verbose_name = _('Log de Notificação')
        verbose_name_plural = _('Logs de Notificações')
        ordering = ['-enviado_em']


class SequenceCounter(models.Model):
    """Contador sequencial thread-safe para gerar números únicos"""
    prefix = models.CharField(max_length=20, unique=True, db_index=True)
    current_value = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'core_sequence_counter'
        verbose_name = 'Contador de Sequência'
        verbose_name_plural = 'Contadores de Sequência'
    
    @classmethod
    def get_next(cls, prefix):
        """
        Retorna próximo número da sequência de forma atômica e robusta.
        Usa select_for_update + F() para incremento atômico no DB.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        MAX_ATTEMPTS = 5
        last_exc = None
        
        for attempt in range(MAX_ATTEMPTS):
            try:
                with transaction.atomic():
                    # get_or_create COM select_for_update para lock
                    counter, created = cls.objects.select_for_update().get_or_create(
                        prefix=prefix,
                        defaults={'current_value': 0}
                    )
                    
                    # Incrementar usando F() para atomicidade no DB
                    counter.current_value = F('current_value') + 1
                    counter.save(update_fields=['current_value'])
                    
                    # Refresh para obter valor real
                    counter.refresh_from_db()
                    
                    return counter.current_value
                    
            except IntegrityError as exc:
                last_exc = exc
                logger.warning(
                    f"SequenceCounter.get_next IntegrityError na tentativa {attempt+1} "
                    f"para '{prefix}': {exc}"
                )
                continue
        
        # Esgotou tentativas
        raise IntegrityError(
            f"Não foi possível obter sequência para '{prefix}' após {MAX_ATTEMPTS} tentativas"
        ) from last_exc
# Importa ComandaStatus criado em core/comanda_status.py para registrar o model no app.
try:
    from .comanda_status import ComandaStatus  # noqa: F401
except Exception:
    # Se houver problema (ex.: erro de sintaxe no arquivo), não quebremos a importação global.
    pass
    
# ============================================================
# SIGNALS - Atualização Automática de Status da Comanda
# ============================================================

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum

@receiver([post_save, post_delete], sender=Pagamento)
def atualizar_status_comanda(sender, instance, **kwargs):
    """
    Atualiza automaticamente o status e data_pagamento da Comanda
    quando um Pagamento é criado, atualizado ou deletado.
    """
    comanda = instance.comanda
    
    # Calcular total pago confirmado
    total_pago = comanda.pagamentos.filter(
        status='confirmado'
    ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
    
    # Calcular valor total da comanda
    valor_comanda = comanda.valor_total
    
    
    # Atualizar status baseado no total pago
    if total_pago >= valor_comanda and valor_comanda > 0:
        comanda.status = Comanda.StatusComanda.PAGA
        # Atualizar data_pagamento com data do último pagamento confirmado
        ultimo_pag = comanda.pagamentos.filter(
            status='confirmado'
        ).order_by('-data_pagamento').first()
        if ultimo_pag:
            comanda.data_pagamento = ultimo_pag.data_pagamento
    elif total_pago > 0:
        comanda.status = Comanda.StatusComanda.PARCIALMENTE_PAGA
        comanda.data_pagamento = None
    else:
        comanda.status = Comanda.StatusComanda.PENDENTE
        comanda.data_pagamento = None
    
    # Salvar alterações
    comanda.save(update_fields=['status', 'data_pagamento', 'updated_at'])
    
