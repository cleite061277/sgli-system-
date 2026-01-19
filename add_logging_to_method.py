import re

with open('core/models_inspection.py', 'r') as f:
    content = f.read()

# Encontrar o início do método get_presigned_url e adicionar logging
# Procurar por: if not self.arquivo:
old_check = """        if not self.arquivo:
            return None"""

new_check = """        import logging
        logger = logging.getLogger(__name__)
        
        if not self.arquivo:
            logger.warning("get_presigned_url: arquivo não existe")
            return None"""

content = content.replace(old_check, new_check)

# Adicionar log antes de verificar credenciais
old_cred_check = """            # Verificar se credenciais R2 estão configuradas
            if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY):
                # Fallback para URL local se R2 não configurado
                return self.arquivo.url"""

new_cred_check = """            # Verificar se credenciais R2 estão configuradas
            logger.info(f"get_presigned_url: Tentando gerar para {self.arquivo.name}")
            has_key = bool(settings.AWS_ACCESS_KEY_ID)
            has_secret = bool(settings.AWS_SECRET_ACCESS_KEY)
            logger.info(f"get_presigned_url: AWS_ACCESS_KEY_ID ok: {has_key}")
            logger.info(f"get_presigned_url: AWS_SECRET_ACCESS_KEY ok: {has_secret}")
            
            if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY):
                logger.warning("get_presigned_url: Credenciais não configuradas - fallback")
                return self.arquivo.url"""

content = content.replace(old_cred_check, new_cred_check)

# Adicionar log após criar cliente
old_client = """            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                region_name='auto'
            )
            
            # Gerar presigned URL"""

new_client = """            logger.info(f"get_presigned_url: Endpoint: {settings.AWS_S3_ENDPOINT_URL}")
            logger.info(f"get_presigned_url: Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                region_name='auto'
            )
            
            logger.info("get_presigned_url: Cliente S3 criado!")
            
            # Gerar presigned URL"""

content = content.replace(old_client, new_client)

# Adicionar log após gerar URL
old_return = """            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': self.arquivo.name
                },
                ExpiresIn=expiration
            )
            
            return url"""

new_return = """            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': self.arquivo.name
                },
                ExpiresIn=expiration
            )
            
            logger.info(f"get_presigned_url: URL gerada! Length: {len(url)}")
            logger.info(f"get_presigned_url: Tem assinatura: {'X-Amz-Algorithm' in url}")
            
            return url"""

content = content.replace(old_return, new_return)

# Melhorar catch de exceção
old_except = """        except Exception as e:
            print(f"Erro ao gerar presigned URL: {e}")
            # Fallback para URL direta
            return self.arquivo.url"""

new_except = """        except Exception as e:
            logger.error(f"get_presigned_url: ERRO {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"get_presigned_url: Traceback: {traceback.format_exc()}")
            # Fallback para URL direta
            return self.arquivo.url"""

content = content.replace(old_except, new_except)

with open('core/models_inspection.py', 'w') as f:
    f.write(content)

print("✅ Logging adicionado com sucesso!")
