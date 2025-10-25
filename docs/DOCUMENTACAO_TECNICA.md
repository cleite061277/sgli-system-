# 🔧 Documentação Técnica - SGLI

## 🏗️ Arquitetura

### Stack Tecnológico
- **Framework:** Django 4.2.8
- **Python:** 3.11
- **Banco:** SQLite (dev) / PostgreSQL (prod)
- **ORM:** Django ORM
- **Admin:** Django Admin (customizado)

### Padrão de Projeto
- **MVC** (Model-View-Controller)
- **MTV** (Model-Template-View) do Django

---

## 📊 Modelos (Models)

### Usuario (CustomUser)
```python
class Usuario(AbstractUser):
    TIPO_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('GERENTE', 'Gerente'),
        ('ATENDENTE', 'Atendente'),
        ('FINANCEIRO', 'Financeiro'),
        ('LOCADOR', 'Locador'),
    ]
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_CHOICES)
    telefone = models.CharField(max_length=20)
    # ... outros campos
```

**Relacionamentos:**
- Herda de `AbstractUser`
- OneToOne com `Locador` (quando tipo=LOCADOR)

---

### Locador
```python
class Locador(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    nome_razao_social = models.CharField(max_length=200)
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    # ... outros campos
```

**Relacionamentos:**
- OneToMany com `Imovel`
- OneToOne com `Usuario` (opcional)

---

### Imovel
```python
class Imovel(models.Model):
    STATUS_CHOICES = [
        ('DISPONIVEL', 'Disponível'),
        ('LOCADO', 'Locado'),
        ('MANUTENCAO', 'Em Manutenção'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    codigo_imovel = models.CharField(max_length=50, unique=True)
    locador = models.ForeignKey(Locador, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    # ... outros campos
```

**Relacionamentos:**
- ManyToOne com `Locador`
- OneToMany com `Locacao`

---

### Locatario
```python
class Locatario(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    nome_razao_social = models.CharField(max_length=200)
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    # ... outros campos
```

**Relacionamentos:**
- OneToMany com `Locacao`

---

### Locacao
```python
class Locacao(models.Model):
    STATUS_CHOICES = [
        ('ATIVA', 'Ativa'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    numero_contrato = models.CharField(max_length=20, unique=True, blank=True)
    imovel = models.ForeignKey(Imovel, on_delete=models.PROTECT)
    locatario = models.ForeignKey(Locatario, on_delete=models.PROTECT)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    valor_aluguel = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    # ... outros campos
    
    def save(self, *args, **kwargs):
        if not self.numero_contrato:
            self.numero_contrato = self.gerar_numero_contrato()
        super().save(*args, **kwargs)
```

**Relacionamentos:**
- ManyToOne com `Imovel`
- ManyToOne com `Locatario`
- OneToMany com `Comanda`

**Métodos:**
- `gerar_numero_contrato()`: Gera número sequencial
- `__str__()`: Representação string

---

### Comanda
```python
class Comanda(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PAGA', 'Paga'),
        ('VENCIDA', 'Vencida'),
        ('CANCELADA', 'Cancelada'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    locacao = models.ForeignKey(Locacao, on_delete=models.CASCADE)
    mes_referencia = models.DateField()
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    # ... outros campos
```

**Relacionamentos:**
- ManyToOne com `Locacao`
- OneToMany com `Pagamento`

---

### Pagamento
```python
class Pagamento(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('CONFIRMADO', 'Confirmado'),
        ('ESTORNADO', 'Estornado'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    comanda = models.ForeignKey(Comanda, on_delete=models.CASCADE)
    data_pagamento = models.DateField()
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2)
    forma_pagamento = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    # ... outros campos
```

**Relacionamentos:**
- ManyToOne com `Comanda`

---

## 🔗 URLs

### Principais Rotas
```python
# sgli_project/urls.py
urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

# core/urls.py
urlpatterns = [
    path('contrato/<uuid:locacao_id>/docx/', gerar_contrato_docx, name='gerar_contrato_docx'),
    path('contrato/<uuid:locacao_id>/pdf/', gerar_contrato_pdf, name='gerar_contrato_pdf'),
]
```

---

## 👁️ Views

### views_gerar_contrato.py

#### gerar_contrato_pdf(request, locacao_id)
**Função:** Gera contrato em PDF

**Parâmetros:**
- `request`: HttpRequest
- `locacao_id`: UUID da locação

**Retorno:** HttpResponse com PDF

**Fluxo:**
1. Busca locação no banco
2. Coleta dados relacionados (imóvel, locatário, locador)
3. Gera PDF com ReportLab
4. Retorna resposta com arquivo

---

#### gerar_contrato_docx(request, locacao_id)
**Função:** Gera contrato em DOCX

**Parâmetros:**
- `request`: HttpRequest
- `locacao_id`: UUID da locação

**Retorno:** HttpResponse com DOCX

**Fluxo:**
1. Busca locação no banco
2. Coleta dados relacionados
3. Gera DOCX com python-docx
4. Retorna resposta com arquivo

---

## 🎨 Admin Customizado

### LocacaoAdmin

**Customizações:**
```python
class LocacaoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_contrato',
        'imovel',
        'locatario',
        'data_inicio',
        'data_fim',
        'valor_aluguel',
        'status',
        'acoes_contrato',
    ]
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Adiciona botões de gerar contrato."""
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj:
            from django.urls import reverse
            extra_context['show_contrato_buttons'] = True
            extra_context['contrato_docx_url'] = reverse('gerar_contrato_docx', args=[obj.pk])
            extra_context['contrato_pdf_url'] = reverse('gerar_contrato_pdf', args=[obj.pk])
        return super().change_view(request, object_id, form_url, extra_context)
```

---

## 📁 Estrutura de Arquivos
```
sgli_system/
├── core/
│   ├── __init__.py
│   ├── models.py                  # Modelos
│   ├── admin.py                   # Admin customizado
│   ├── views_gerar_contrato.py    # Views de contrato
│   ├── urls.py                    # URLs da app
│   ├── apps.py                    # Config da app
│   └── templates/
│       └── admin/
│           └── core/
│               └── locacao/
│                   └── change_form.html
├── sgli_project/
│   ├── __init__.py
│   ├── settings.py                # Configurações
│   ├── urls.py                    # URLs principais
│   └── wsgi.py                    # WSGI config
├── templates/
├── static/
├── media/
├── db.sqlite3
├── manage.py
└── requirements.txt
```

---

## 🔧 Configurações (settings.py)

### Principais Configurações
```python
# Apps instalados
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

# Modelo de usuário customizado
AUTH_USER_MODEL = 'core.Usuario'

# Banco de dados
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Arquivos de mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

---

## 🗄️ Migrações

### Comandos Úteis
```bash
# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Ver SQL das migrações
python manage.py sqlmigrate core 0001

# Listar migrações
python manage.py showmigrations
```

---

## 🧪 Testes

### Estrutura de Testes
```python
# core/tests.py
from django.test import TestCase
from .models import Locacao, Imovel, Locatario

class LocacaoTestCase(TestCase):
    def setUp(self):
        # Setup inicial
        pass
    
    def test_gerar_numero_contrato(self):
        # Teste de geração de número
        pass
```

### Executar Testes
```bash
python manage.py test
```

---

## 📦 Dependências

### requirements.txt
```
Django==4.2.8
Pillow==10.1.0
reportlab==4.0.7
python-docx==1.1.0
docxcompose==1.4.0
```

---

## 🚀 Deploy (Produção)

### Checklist

1. **Configurações de Segurança:**
```python
DEBUG = False
ALLOWED_HOSTS = ['seu-dominio.com']
SECRET_KEY = 'chave-segura-aqui'
```

2. **Banco de Dados:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sgli_db',
        'USER': 'sgli_user',
        'PASSWORD': 'senha-forte',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

3. **Arquivos Estáticos:**
```bash
python manage.py collectstatic
```

4. **WSGI/ASGI:**
- Use Gunicorn ou uWSGI
- Configure Nginx como reverse proxy

---

## 🔐 Segurança

### Boas Práticas Implementadas

1. **CSRF Protection:** Ativo por padrão
2. **SQL Injection:** Protegido pelo Django ORM
3. **XSS:** Auto-escape de templates
4. **Permissões:** Por tipo de usuário
5. **UUIDs:** Chaves primárias não sequenciais

---

## 📈 Performance

### Otimizações

1. **select_related/prefetch_related:** Em listagens
2. **Índices:** Em campos de busca frequente
3. **Cache:** Considerar para produção
4. **Compressão:** De arquivos estáticos

---

## 🐛 Debug

### Ferramentas

1. **Django Debug Toolbar** (desenvolvimento)
2. **Logs:** Configure logging em settings.py
3. **Shell:** `python manage.py shell`

---

## 🔄 Versionamento

### Git
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <repo-url>
git push -u origin main
```

---

## 📞 API (Futuro)

### Django REST Framework
```bash
pip install djangorestframework
```

Endpoints sugeridos:
- `/api/locacoes/`
- `/api/imoveis/`
- `/api/locatarios/`
- `/api/pagamentos/`

---

© 2025 SGLI System - Documentação Técnica
