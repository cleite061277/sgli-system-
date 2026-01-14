"""
Serviço de Geração de PDF para Vistorias
Usa ReportLab (pure Python, sem dependências de SO)
Autor: Claude + Cícero (Policorp)
Data: 11/01/2026
"""
from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from django.utils import timezone
from django.core.files.base import ContentFile
from django.conf import settings
import os
from django.conf import settings
import os


def gerar_pdf_vistoria(inspection):
    """
    Gera PDF completo da vistoria com capa e fotos
    
    Args:
        inspection: Objeto Inspection com fotos relacionadas
    
    Returns:
        tuple: (ContentFile com PDF, número de páginas)
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Dados da vistoria
    locacao = inspection.locacao
    imovel = locacao.imovel
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
    c.drawCentredString(width/2, height - 5.5*cm, "RELATÓRIO DE VISTORIA")
    
    # Linha decorativa (mais abaixo)
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
    c.drawString(7*cm, y, nome_locatario)
    
    y -= 0.8*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(3*cm, y, "Imóvel:")
    c.setFont("Helvetica", 12)
    endereco = f"{imovel.endereco}, {imovel.numero}"
    c.drawString(7*cm, y, endereco[:50])
    
    y -= 0.8*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(3*cm, y, "Bairro:")
    c.setFont("Helvetica", 12)
    c.drawString(7*cm, y, imovel.bairro)
    
    y -= 0.8*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(3*cm, y, "Cidade:")
    c.setFont("Helvetica", 12)
    c.drawString(7*cm, y, f"{imovel.cidade} - {imovel.estado}")
    
    # Linha separadora
    y -= 1*cm
    c.setStrokeColor(colors.HexColor("#ddd"))
    c.setLineWidth(1)
    c.line(3*cm, y, width - 3*cm, y)
    
    # Informações da vistoria
    y -= 1*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(3*cm, y, "Vistoria:")
    c.setFont("Helvetica", 12)
    c.drawString(7*cm, y, inspection.titulo)
    
    if inspection.inspector_nome:
        y -= 0.8*cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(3*cm, y, "Inspector:")
        c.setFont("Helvetica", 12)
        c.drawString(7*cm, y, inspection.inspector_nome)
    
    y -= 0.8*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(3*cm, y, "Data:")
    c.setFont("Helvetica", 12)
    data_formatada = timezone.now().strftime('%d/%m/%Y às %H:%M')
    c.drawString(7*cm, y, data_formatada)
    
    # Descrição/Observações (se houver)
    if inspection.descricao:
        y -= 1.5*cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(3*cm, y, "Observações:")
        
        y -= 0.6*cm
        c.setFont("Helvetica", 10)
        
        # Quebrar texto em múltiplas linhas
        descricao_linhas = _quebrar_texto(inspection.descricao, 80)
        for linha in descricao_linhas[:5]:  # Máximo 5 linhas na capa
            c.drawString(3*cm, y, linha)
            y -= 0.5*cm
    
    # Rodapé atualizado
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
    )
    
    c.showPage()  # Finalizar capa
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PÁGINAS 2-N: FOTOS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    fotos = list(inspection.fotos.all().order_by('ordem', 'tirada_em'))
    total_fotos = len(fotos)
    
    for idx, foto in enumerate(fotos, start=1):
        try:
            # Abrir imagem do storage (R2 ou local)
            foto.imagem.open('rb')
            img_data = foto.imagem.read()
            foto.imagem.close()
            
            img = Image.open(BytesIO(img_data))
            img = img.convert("RGB")
            
            # Thumbnail para otimizar (já está comprimida, mas garantir)
            img.thumbnail((1600, 1600), Image.LANCZOS)
            
            # Criar ImageReader para ReportLab
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=85, optimize=True)
            img_buffer.seek(0)
            image_reader = ImageReader(img_buffer)
            
            # Calcular dimensões para caber no A4
            margin = 2*cm
            header_space = 2*cm
            footer_space = 3*cm
            
            usable_w = width - 2*margin
            usable_h = height - header_space - footer_space
            
            iw, ih = img.size
            ratio = min(usable_w/iw, usable_h/ih)
            draw_w = iw * ratio
            draw_h = ih * ratio
            
            # Centralizar imagem
            x = (width - draw_w) / 2
            y = footer_space + (usable_h - draw_h) / 2
            
            # Cabeçalho
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(colors.black)
            c.drawString(margin, height - margin, f"Foto {idx}/{total_fotos}")
            
            # Linha abaixo do cabeçalho
            c.setStrokeColor(colors.HexColor("#ddd"))
            c.setLineWidth(0.5)
            c.line(margin, height - margin - 0.3*cm, width - margin, height - margin - 0.3*cm)
            
            # Desenhar imagem
            c.drawImage(
                image_reader,
                x, y,
                width=draw_w,
                height=draw_h,
                preserveAspectRatio=True
            )
            
            # Rodapé com legenda
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(colors.black)
            
            if foto.legenda:
                legenda_texto = f"Legenda: {foto.legenda[:80]}"
                c.drawString(margin, margin + 1.2*cm, legenda_texto)
            
            # Data/hora
            c.setFont("Helvetica", 9)
            c.setFillColor(colors.HexColor("#666"))
            data_foto = foto.tirada_em.strftime('%d/%m/%Y às %H:%M')
            c.drawString(margin, margin + 0.6*cm, f"Registrada em: {data_foto}")
            
            # Informações técnicas
            info_tecnica = f"Resolução: {foto.largura}x{foto.altura}px | Tamanho: {foto.tamanho_mb} MB"
            c.drawString(margin, margin + 0.2*cm, info_tecnica)
            
            c.showPage()  # Próxima foto
            
        except Exception as e:
            # Se der erro em uma foto, continuar com as outras
            print(f"⚠️  Erro ao processar foto {idx}: {e}")
            continue
    
    # Finalizar PDF
    c.save()
    buffer.seek(0)
    
    total_paginas = total_fotos + 1  # Capa + fotos
    
    # Retornar como ContentFile para salvar no modelo
    pdf_file = ContentFile(buffer.read())
    
    return pdf_file, total_paginas


def _quebrar_texto(texto, max_chars):
    """
    Quebra texto em linhas de no máximo max_chars caracteres
    """
    palavras = texto.split()
    linhas = []
    linha_atual = ""
    
    for palavra in palavras:
        if len(linha_atual) + len(palavra) + 1 <= max_chars:
            linha_atual += palavra + " "
        else:
            if linha_atual:
                linhas.append(linha_atual.strip())
            linha_atual = palavra + " "
    
    if linha_atual:
        linhas.append(linha_atual.strip())
    
    return linhas
