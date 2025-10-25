"""
Conversor de templates ODT para processamento.
"""
import os
import zipfile
import xml.etree.ElementTree as ET
from docx import Document
from docx.shared import Pt

def converter_odt_para_docx(odt_path, docx_path):
    """
    Converter arquivo ODT para DOCX mantendo variáveis de template.
    Implementação básica - converte texto simples.
    """
    try:
        from odf import text, teletype
        from odf.opendocument import load
        
        # Carregar ODT
        doc_odt = load(odt_path)
        
        # Criar DOCX
        doc_docx = Document()
        
        # Extrair texto do ODT preservando variáveis {{ }}
        for paragraph in doc_odt.getElementsByType(text.P):
            texto = teletype.extractText(paragraph)
            if texto.strip():
                doc_docx.add_paragraph(texto)
        
        # Salvar DOCX
        doc_docx.save(docx_path)
        return True
        
    except Exception as e:
        print(f"Erro ao converter ODT: {e}")
        return False

def processar_template_odt(odt_path, context):
    """
    Processar template ODT substituindo variáveis.
    Converte para DOCX temporariamente para usar docxtpl.
    """
    import tempfile
    from docxtpl import DocxTemplate
    
    # Criar arquivo temporário DOCX
    temp_docx = tempfile.NamedTemporaryFile(suffix='.docx', delete=False)
    temp_docx.close()
    
    try:
        # Converter ODT -> DOCX
        if converter_odt_para_docx(odt_path, temp_docx.name):
            # Processar com docxtpl
            doc = DocxTemplate(temp_docx.name)
            doc.render(context)
            return doc
        else:
            raise Exception("Falha na conversão ODT para DOCX")
    finally:
        # Limpar arquivo temporário
        if os.path.exists(temp_docx.name):
            os.unlink(temp_docx.name)
