from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'SGLI - Sistema Core'
    
    def ready(self):
        """
        Executado quando o Django inicializa a aplicação
        Registra signals e inicia o scheduler de notificações
        """
        # 1. Registra signals (receivers)
        try:
            import core.signals
            logger.info("✅ Signals registrados com sucesso")
        except Exception as e:
            logger.warning(f"⚠️  Falha ao registrar signals: {str(e)}")
            pass
        
        # 2. Injeta métodos/props da Comanda em runtime
        try:
            import core.comanda_extensions as _ce
            try:
                _ce.bind()
                logger.info("✅ Comanda extensions carregados")
            except Exception as e:
                logger.warning(f"⚠️  Falha ao carregar comanda_extensions: {str(e)}")
                pass
        except Exception:
            pass
        
        # 3. Inicia APScheduler para notificações automáticas
        # IMPORTANTE: Só inicia em ambientes de produção/desenvolvimento
        # Não inicia durante migrações, testes ou comandos management
        import sys
        run_scheduler = (
            'runserver' in sys.argv or 
            'gunicorn' in sys.argv[0] or
            '--noreload' in sys.argv
        )
        
        if run_scheduler:
            try:
                from core.scheduler import start_scheduler
                start_scheduler()
                logger.info("🚀 APScheduler de notificações iniciado!")
            except Exception as e:
                logger.error(f"❌ Erro ao iniciar scheduler: {str(e)}")
        else:
            logger.info("ℹ️  Scheduler não iniciado (comando de management ou teste)")
