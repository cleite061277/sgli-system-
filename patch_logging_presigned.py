"""
Adicionar logging detalhado no get_presigned_url()
"""

with open('core/models_inspection.py', 'r') as f:
    content = f.read()

# Encontrar e substituir o método get_presigned_url
old_method = """    def get_presigned_url(self, expiration=604800):
        """
        Gera URL assinada temporária para download do PDF
        
        Args:
            expiration: Tempo de validade em segundos (padrão: 7 dias = 604800)
        
        Returns:
            URL assinada ou URL direta como fallback
        """
        if not self.arquivo:
            return None
        
        try:
            import boto3
            from django.conf import settings
            
            # Verificar se credenciais R2 estão configuradas
            if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY):
                # Fallback para URL local se R2 não configurado
                return self.arquivo.url
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                region_name='auto'
            )
            
            # Gerar presigned URL
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': self.arquivo.name
                },
                ExpiresIn=expiration
            )
            
            return url
            
        except Exception as e:
            print(f"Erro ao gerar presigned URL: {e}")
            # Fallback para URL direta
            return self.arquivo.url"""

new_method = """    def get_presigned_url(self, expiration=604800):
        """
        Gera URL assinada temporária para download do PDF
        
        Args:
            expiration: Tempo de validade em segundos (padrão: 7 dias = 604800)
        
        Returns:
            URL assinada ou URL direta como fallback
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.arquivo:
            logger.warning("get_presigned_url: arquivo não existe")
            return None
        
        try:
            import boto3
            from django.conf import settings
            
            logger.info(f"get_presigned_url: Tentando gerar presigned URL para {self.arquivo.name}")
            
            # Verificar se credenciais R2 estão configuradas
            has_key = bool(settings.AWS_ACCESS_KEY_ID)
            has_secret = bool(settings.AWS_SECRET_ACCESS_KEY)
            logger.info(f"get_presigned_url: AWS_ACCESS_KEY_ID configurado: {has_key}")
            logger.info(f"get_presigned_url: AWS_SECRET_ACCESS_KEY configurado: {has_secret}")
            
            if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY):
                logger.warning("get_presigned_url: Credenciais R2 não configuradas - usando fallback")
                return self.arquivo.url
            
            logger.info(f"get_presigned_url: Endpoint: {settings.AWS_S3_ENDPOINT_URL}")
            logger.info(f"get_presigned_url: Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                region_name='auto'
            )
            
            logger.info("get_presigned_url: Cliente S3 criado com sucesso")
            
            # Gerar presigned URL
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': self.arquivo.name
                },
                ExpiresIn=expiration
            )
            
            logger.info(f"get_presigned_url: Presigned URL gerada com sucesso (length: {len(url)})")
            logger.info(f"get_presigned_url: URL contém X-Amz-Algorithm: {'X-Amz-Algorithm' in url}")
            
            return url
            
        except Exception as e:
            logger.error(f"get_presigned_url: ERRO ao gerar presigned URL: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"get_presigned_url: Traceback: {traceback.format_exc()}")
            # Fallback para URL direta
            return self.arquivo.url"""

if old_method in content:
    content = content.replace(old_method, new_method)
    
    with open('core/models_inspection.py', 'w') as f:
        f.write(content)
    
    print("✅ Logging detalhado adicionado ao get_presigned_url()")
else:
    print("⚠️ Método não encontrado para substituir")
    print("ℹ️ Pode já estar atualizado ou estrutura diferente")

