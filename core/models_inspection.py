"""
Models para Sistema de Vistorias (Inspections)
Autor: Claude + Cícero (Policorp)
Data: 11/01/2026
"""
import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.urls import reverse


def upload_inspection_photo_path(instance, filename):
    """
    Define caminho de upload para fotos de vistoria
    tenant_001/vistorias/{inspection_id}/photos/{filename}
    """
    inspection_id = instance.inspection.id
    # TODO: Multi-tenant - pegar tenant_id do proprietário
    tenant_id = "tenant_001"  # Por enquanto fixo
    return f"{tenant_id}/vistorias/{inspection_id}/photos/{filename}"


def upload_inspection_pdf_path(instance, filename):
    """
    Define caminho de upload para PDF de vistoria
    tenant_001/vistorias/{inspection_id}/pdf/{filename}
    """
    inspection_id = instance.inspection.id
    tenant_id = "tenant_001"  # Por enquanto fixo
    return f"{tenant_id}/vistorias/{inspection_id}/pdf/{filename}"


class Inspection(models.Model):
    """
    Vistoria de imóvel (entrada, saída, periódica)
    """
    
    STATUS_CHOICES = [
        ('scheduled', 'Agendada'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluída'),
        ('cancelled', 'Cancelada'),
    ]
    
    # Identificação
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Relacionamento com Contrato
    locacao = models.ForeignKey(
        'Locacao',
        on_delete=models.CASCADE,
        related_name='vistorias',
        verbose_name='Contrato'
    )
    
    # Relacionamento com Renovação (OPCIONAL)
    renovacao = models.ForeignKey(
        'RenovacaoContrato',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vistorias',
        verbose_name='Renovação Relacionada',
        help_text='Se esta vistoria foi feita por causa de uma renovação'
    )
    
    # Informações da Vistoria
    titulo = models.CharField(
        max_length=100,
        verbose_name='Título',
        help_text='Ex: Vistoria de Entrada, Vistoria de Saída'
    )
    
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descrição/Observações',
        help_text='Observações gerais sobre a vistoria'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name='Status'
    )
    
    # Token para acesso público mobile
    token = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name='Token de Acesso'
    )
    
    token_expires_at = models.DateTimeField(
        verbose_name='Token Expira Em',
        help_text='Data de expiração do token de acesso'
    )
    
    # Inspector (pessoa que faz a vistoria)
    inspector_nome = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Nome do Inspector'
    )
    
    inspector_contato = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Contato do Inspector',
        help_text='Telefone ou email'
    )
    
    # Timestamps
    scheduled_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Agendada Em'
    )
    
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Iniciada Em'
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Concluída Em'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado Em'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado Em'
    )
    
    class Meta:
        verbose_name = 'Vistoria'
        verbose_name_plural = 'Vistorias'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.titulo} - {self.locacao.numero_contrato}"
    
    def save(self, *args, **kwargs):
        """Override save para gerar token automaticamente"""
        if not self.token:
            self.token = uuid.uuid4().hex
        
        if not self.token_expires_at:
            self.token_expires_at = timezone.now() + timedelta(days=7)
        
        super().save(*args, **kwargs)
    
    @property
    def is_token_valid(self):
        """Verifica se token ainda é válido"""
        return timezone.now() < self.token_expires_at
    
    @property
    def total_fotos(self):
        """Total de fotos cadastradas"""
        return self.fotos.count()
    
    @property
    def has_pdf(self):
        """Verifica se já tem PDF gerado"""
        return hasattr(self, 'pdf') and self.pdf.arquivo
    
    def get_public_url(self, request=None):
        """Retorna URL pública para acesso mobile"""
        path = reverse('inspection_mobile_form', kwargs={'token': self.token})
        if request:
            return request.build_absolute_uri(path)
        else:
            from django.conf import settings
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            return f"{site_url}{path}"
    
    def mark_started(self):
        """Marca vistoria como iniciada"""
        if not self.started_at:
            self.started_at = timezone.now()
            self.status = 'in_progress'
            self.save(update_fields=['started_at', 'status', 'updated_at'])
    
    def mark_completed(self):
        """Marca vistoria como concluída"""
        self.completed_at = timezone.now()
        self.status = 'completed'
        self.save(update_fields=['completed_at', 'status', 'updated_at'])
    
    def renovar_token(self, dias=7):
        """Renova token de acesso"""
        self.token = uuid.uuid4().hex
        self.token_expires_at = timezone.now() + timedelta(days=dias)
        self.save(update_fields=['token', 'token_expires_at', 'updated_at'])
        return self.token


class InspectionPhoto(models.Model):
    """
    Foto individual de vistoria
    NOTA: Fotos são TEMPORÁRIAS e deletadas após geração do PDF
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    inspection = models.ForeignKey(
        Inspection,
        on_delete=models.CASCADE,
        related_name='fotos',
        verbose_name='Vistoria'
    )
    
    # Arquivo da imagem (armazenado no R2)
    imagem = models.ImageField(
        upload_to=upload_inspection_photo_path,
        verbose_name='Imagem'
    )
    
    legenda = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Legenda',
        help_text='Ex: Sala - Parede norte'
    )
    
    ordem = models.PositiveIntegerField(
        default=1,
        verbose_name='Ordem',
        help_text='Ordem de exibição no relatório'
    )
    
    # Metadados da imagem
    largura = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Largura (px)'
    )
    
    altura = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Altura (px)'
    )
    
    tamanho_bytes = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Tamanho (bytes)'
    )
    
    tirada_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Tirada Em'
    )
    
    class Meta:
        verbose_name = 'Foto de Vistoria'
        verbose_name_plural = 'Fotos de Vistoria'
        ordering = ['ordem', 'tirada_em']
        indexes = [
            models.Index(fields=['inspection', 'ordem']),
        ]
    
    def __str__(self):
        return f"Foto {self.ordem} - {self.inspection.titulo}"
    
    @property
    def tamanho_mb(self):
        """Retorna tamanho em MB"""
        if self.tamanho_bytes:
            return round(self.tamanho_bytes / (1024 * 1024), 2)
        return 0


class InspectionPDF(models.Model):
    """
    PDF gerado da vistoria (permanente)
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    inspection = models.OneToOneField(
        Inspection,
        on_delete=models.CASCADE,
        related_name='pdf',
        verbose_name='Vistoria'
    )
    
    # Arquivo PDF (armazenado no R2)
    arquivo = models.FileField(
        upload_to=upload_inspection_pdf_path,
        verbose_name='Arquivo PDF'
    )
    
    # Metadados do PDF
    paginas = models.PositiveIntegerField(
        verbose_name='Número de Páginas'
    )
    
    tamanho_bytes = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Tamanho (bytes)'
    )
    
    gerado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Gerado Em'
    )
    
    class Meta:
        verbose_name = 'PDF de Vistoria'
        verbose_name_plural = 'PDFs de Vistoria'
    
    def __str__(self):
        return f"PDF - {self.inspection.titulo}"
    
    @property
    def tamanho_mb(self):
        """Retorna tamanho em MB"""
        if self.tamanho_bytes:
            return round(self.tamanho_bytes / (1024 * 1024), 2)
        return 0
    
    @property
    def nome_arquivo(self):
        """Retorna nome do arquivo"""
        if self.arquivo:
            return self.arquivo.name.split('/')[-1]
        return ''
