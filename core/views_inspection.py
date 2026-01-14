"""
Views para Sistema de Vistorias (Mobile Interface)
Autor: Claude + Cícero (Policorp)
Data: 11/01/2026
"""
from io import BytesIO
from PIL import Image
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.utils import timezone
from core.models_inspection import Inspection, InspectionPhoto, InspectionPDF
from core.services.inspection_pdf import gerar_pdf_vistoria


@require_http_methods(["GET"])
def abrir_vistoria_mobile(request, token):
    """
    View pública para abrir formulário mobile de vistoria
    Acessível via link com token (sem autenticação)
    """
    inspection = get_object_or_404(Inspection, token=token)
    
    # Verificar se token ainda é válido
    if not inspection.is_token_valid:
        return render(request, 'inspection/token_expirado.html', {
            'inspection': inspection
        })
    
    # Marcar como iniciada (se ainda não foi)
    if inspection.status == 'scheduled':
        inspection.mark_started()
    
    # Contexto para template
    context = {
        'inspection': inspection,
        'locacao': inspection.locacao,
        'imovel': inspection.locacao.imovel,
        'fotos': inspection.fotos.all().order_by('ordem'),
        'total_fotos': inspection.total_fotos,
        'max_fotos': 50,  # Limite de fotos
        'has_pdf': inspection.has_pdf,
        'pdf_url': inspection.pdf.get_presigned_url() if inspection.has_pdf else None,
    }
    
    return render(request, 'inspection/mobile_form.html', context)


@csrf_exempt  # Token já fornece segurança
@require_http_methods(["POST"])
def upload_foto_vistoria(request, token):
    """
    Upload de foto via mobile (AJAX)
    Comprime imagem e salva no R2
    """
    inspection = get_object_or_404(Inspection, token=token)
    
    # Verificar token
    if not inspection.is_token_valid:
        return JsonResponse({
            'success': False,
            'error': 'Token expirado'
        }, status=403)
    
    # Verificar se vistoria já foi finalizada
    if inspection.status == 'completed':
        return JsonResponse({
            'success': False,
            'error': 'Vistoria já foi finalizada'
        }, status=400)
    
    # Verificar limite de fotos
    if inspection.total_fotos >= 50:
        return JsonResponse({
            'success': False,
            'error': 'Limite de 50 fotos atingido'
        }, status=400)
    
    # Pegar arquivo do upload
    arquivo_foto = request.FILES.get('foto')
    if not arquivo_foto:
        return JsonResponse({
            'success': False,
            'error': 'Nenhuma foto enviada'
        }, status=400)
    
    # Pegar metadados
    legenda = request.POST.get('legenda', '')
    ordem = int(request.POST.get('ordem', inspection.total_fotos + 1))
    
    try:
        # Abrir imagem com Pillow
        img = Image.open(arquivo_foto)
        img = img.convert("RGB")
        
        # Pegar dimensões originais
        largura_original, altura_original = img.size
        
        # Redimensionar para máximo 1600px (mantém proporção)
        max_dimension = 1600
        if largura_original > max_dimension or altura_original > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
        
        # Comprimir e salvar em buffer
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=75, optimize=True)
        tamanho_bytes = buffer.tell()
        buffer.seek(0)
        
        # Verificar tamanho máximo (1.5 MB)
        if tamanho_bytes > 1.5 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'Foto muito grande (máx 1.5 MB após compressão)'
            }, status=400)
        
        # Criar objeto InspectionPhoto
        foto = InspectionPhoto(
            inspection=inspection,
            legenda=legenda,
            ordem=ordem,
            largura=img.size[0],
            altura=img.size[1],
            tamanho_bytes=tamanho_bytes
        )
        
        # Salvar imagem (django-storages vai para R2 automaticamente)
        filename = f"{inspection.id}-{ordem}.jpg"
        foto.imagem.save(filename, ContentFile(buffer.read()), save=True)
        
        return JsonResponse({
            'success': True,
            'foto_id': str(foto.id),
            'ordem': foto.ordem,
            'tamanho_mb': foto.tamanho_mb,
            'total_fotos': inspection.total_fotos
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao processar imagem: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def deletar_foto_vistoria(request, token, foto_id):
    """
    Deletar foto específica (antes de finalizar)
    """
    inspection = get_object_or_404(Inspection, token=token)
    
    # Verificar token
    if not inspection.is_token_valid:
        return JsonResponse({
            'success': False,
            'error': 'Token expirado'
        }, status=403)
    
    # Verificar se vistoria já foi finalizada
    if inspection.status == 'completed':
        return JsonResponse({
            'success': False,
            'error': 'Não é possível deletar fotos após finalizar'
        }, status=400)
    
    try:
        foto = get_object_or_404(InspectionPhoto, id=foto_id, inspection=inspection)
        
        # Deletar arquivo do R2
        foto.imagem.delete()
        
        # Deletar objeto
        foto.delete()
        
        return JsonResponse({
            'success': True,
            'total_fotos': inspection.total_fotos
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def finalizar_vistoria(request, token):
    """
    Finalizar vistoria e gerar PDF
    Deleta fotos brutas após gerar PDF
    """
    inspection = get_object_or_404(Inspection, token=token)
    
    # Verificar token
    if not inspection.is_token_valid:
        return JsonResponse({
            'success': False,
            'error': 'Token expirado'
        }, status=403)
    
    # Verificar se já foi finalizada
    if inspection.status == 'completed':
        return JsonResponse({
            'success': False,
            'error': 'Vistoria já foi finalizada'
        }, status=400)
    
    # Verificar se tem fotos
    if inspection.total_fotos == 0:
        return JsonResponse({
            'success': False,
            'error': 'É necessário pelo menos 1 foto para finalizar'
        }, status=400)
    
    try:
        # Gerar PDF
        pdf_content, total_paginas = gerar_pdf_vistoria(inspection)
        
        # Salvar PDF no R2
        filename = f"Vistoria_{inspection.locacao.numero_contrato}_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
        
        # Criar ou atualizar InspectionPDF
        if hasattr(inspection, 'pdf') and inspection.pdf:
            # Atualizar existente
            pdf_obj = inspection.pdf
            pdf_obj.arquivo.delete()  # Deletar PDF antigo
            pdf_obj.arquivo.save(filename, pdf_content, save=False)
            pdf_obj.paginas = total_paginas
            pdf_obj.tamanho_bytes = pdf_content.size
            pdf_obj.save()
        else:
            # Criar novo
            pdf_obj = InspectionPDF(
                inspection=inspection,
                paginas=total_paginas,
                tamanho_bytes=pdf_content.size
            )
            pdf_obj.arquivo.save(filename, pdf_content, save=True)
        
        # Deletar fotos brutas do R2 (economia de espaço)
        fotos = inspection.fotos.all()
        for foto in fotos:
            try:
                foto.imagem.delete(save=False)  # Deletar do R2
            except:
                pass  # Se já foi deletado, ignorar
            foto.delete()  # Deletar do banco
        
        # Marcar vistoria como concluída
        inspection.mark_completed()
        
        # URL do PDF
        pdf_url = pdf_obj.arquivo.url if pdf_obj.arquivo else None
        
        return JsonResponse({
            'success': True,
            'message': 'Vistoria finalizada com sucesso!',
            'pdf_url': pdf_url,
            'pdf_filename': pdf_obj.nome_arquivo,
            'pdf_pages': pdf_obj.paginas,
            'pdf_size_mb': pdf_obj.tamanho_mb
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao finalizar: {str(e)}'
        }, status=500)
