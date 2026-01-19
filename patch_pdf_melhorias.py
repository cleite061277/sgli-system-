"""
Melhorias no PDF de Vistoria:
1. Logo HABITAT PRO no topo
2. Nome do locatário após número do contrato
3. Rodapé atualizado
"""

with open('core/services/inspection_pdf.py', 'r') as f:
    content = f.read()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MELHORIA 1: Adicionar import de settings no topo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

old_imports = """from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from django.utils import timezone
from django.core.files.base import ContentFile"""

new_imports = """from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from django.utils import timezone
from django.core.files.base import ContentFile
from django.conf import settings
import os"""

content = content.replace(old_imports, new_imports)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MELHORIA 2: Adicionar logo após "PÁGINA 1: CAPA"
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

old_capa = """    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PÁGINA 1: CAPA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Título principal
    c.setFillColor(colors.HexColor("#333"))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 3*cm, "RELATÓRIO DE VISTORIA")"""

new_capa = """    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PÁGINA 1: CAPA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Logo HABITAT PRO no topo
    try:
        logo_path = os.path.join(settings.MEDIA_ROOT, 'logos', 'habitat_pro_logo.png')
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            # Logo centralizado: 8cm de largura
            logo_width = 8*cm
            logo_height = 2*cm  # Altura proporcional
            logo_x = (width - logo_width) / 2
            logo_y = height - 3*cm
            c.drawImage(logo, logo_x, logo_y, width=logo_width, height=logo_height, 
                       preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print(f"⚠️  Logo não carregado: {e}")
    
    # Título principal (mais abaixo por causa do logo)
    c.setFillColor(colors.HexColor("#333"))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 5.5*cm, "RELATÓRIO DE VISTORIA")"""

content = content.replace(old_capa, new_capa)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MELHORIA 3: Adicionar nome locatário e ajustar posições
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

old_linha = """    # Linha decorativa
    c.setStrokeColor(colors.HexColor("#667eea"))
    c.setLineWidth(2)
    c.line(4*cm, height - 3.5*cm, width - 4*cm, height - 3.5*cm)
    
    # Informações do contrato
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    y = height - 5*cm
    
    c.drawString(3*cm, y, "Contrato:")
    c.setFont("Helvetica", 12)
    c.drawString(7*cm, y, locacao.numero_contrato)"""

new_linha = """    # Linha decorativa (mais abaixo)
    c.setStrokeColor(colors.HexColor("#667eea"))
    c.setLineWidth(2)
    c.line(4*cm, height - 6*cm, width - 4*cm, height - 6*cm)
    
    # Informações do contrato
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    y = height - 7.5*cm
    
    c.drawString(3*cm, y, "Contrato:")
    c.setFont("Helvetica", 12)
    c.drawString(7*cm, y, locacao.numero_contrato)
    
    # Nome do Locatário (NOVO)
    y -= 0.8*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(3*cm, y, "Locatário:")
    c.setFont("Helvetica", 12)
    nome_locatario = locacao.locatario.nome_razao_social[:50]  # Limitar tamanho
    c.drawString(7*cm, y, nome_locatario)"""

content = content.replace(old_linha, new_linha)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MELHORIA 4: Atualizar rodapé
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

old_rodape = """    # Rodapé
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.HexColor("#666"))
    c.drawCentredString(
        width/2, 
        2*cm, 
        "HABITAT PRO - Sistema de Gestão de Locações"
    )
    c.drawCentredString(
        width/2, 
        1.5*cm, 
        "Policorp Imóveis | Paranaguá - PR"
    )"""

new_rodape = """    # Rodapé atualizado
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#666"))
    c.drawCentredString(
        width/2, 
        1.5*cm, 
        "HABITAT PRO v1.0 | Sistema de Gestão Imobiliária"
    )
    c.drawCentredString(
        width/2, 
        1*cm, 
        "© 2025 A&C Imóveis e Sistemas Imobiliários | Paranaguá - PR"
    )"""

content = content.replace(old_rodape, new_rodape)

# Salvar arquivo modificado
with open('core/services/inspection_pdf.py', 'w') as f:
    f.write(content)

print("✅ Patch aplicado com sucesso!")
print("")
print("📋 MELHORIAS IMPLEMENTADAS:")
print("   1. ✅ Logo HABITAT PRO no topo da capa")
print("   2. ✅ Nome do locatário após número do contrato")
print("   3. ✅ Rodapé atualizado com novo texto")
print("")
print("🧪 VALIDAR:")
print("   python -m py_compile core/services/inspection_pdf.py")

