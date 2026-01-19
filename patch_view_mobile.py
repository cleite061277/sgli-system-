"""
Adicionar pdf_url ao contexto da view mobile
"""

with open('core/views_inspection.py', 'r') as f:
    content = f.read()

# Encontrar o contexto da view abrir_vistoria_mobile
old_context = """    # Contexto para template
    context = {
        'inspection': inspection,
        'locacao': inspection.locacao,
        'imovel': inspection.locacao.imovel,
        'fotos': inspection.fotos.all().order_by('ordem'),
        'total_fotos': inspection.total_fotos,
        'max_fotos': 50,  # Limite de fotos
        'has_pdf': inspection.has_pdf,
    }"""

new_context = """    # Contexto para template
    context = {
        'inspection': inspection,
        'locacao': inspection.locacao,
        'imovel': inspection.locacao.imovel,
        'fotos': inspection.fotos.all().order_by('ordem'),
        'total_fotos': inspection.total_fotos,
        'max_fotos': 50,  # Limite de fotos
        'has_pdf': inspection.has_pdf,
        'pdf_url': inspection.pdf.get_presigned_url() if inspection.has_pdf else None,
    }"""

if old_context in content:
    content = content.replace(old_context, new_context)
    
    with open('core/views_inspection.py', 'w') as f:
        f.write(content)
    
    print("✅ View atualizada - pdf_url adicionado ao contexto")
else:
    print("⚠️ Contexto não encontrado - pode estar diferente")
    print("Vou mostrar o contexto atual:")
    import re
    match = re.search(r'# Contexto para template.*?}', content, re.DOTALL)
    if match:
        print(match.group(0))

