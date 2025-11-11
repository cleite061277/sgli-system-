from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # registra signals (receivers)
        try:
            import core.signals  # registra os receivers
        except Exception:
            pass

        # injeta métodos/props da Comanda em runtime (comanda_extensions.bind)
        try:
            import core.comanda_extensions as _ce
            try:
                _ce.bind()
            except Exception:
                # bind pode falhar em tempos de importação precoce; não quebrar a app
                pass
        except Exception:
            pass

        # nome legível do app no admin (mantive sua linha original)
        verbose_name = 'SGLI - Sistema Core'
