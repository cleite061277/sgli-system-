# core/utils/recibo_links.py
from django.core import signing
from django.urls import reverse
from django.conf import settings
import time

# Salt para assinatura — configure em settings.py se desejar
SIGNING_SALT = getattr(settings, "RECIBO_SIGNING_SALT", "recibo-salt")
# Tempo de validade em segundos (padrão 24h)
TOKEN_MAX_AGE = getattr(settings, "RECIBO_TOKEN_MAX_AGE", 60 * 60 * 24)


def make_recibo_token(pagamento_id: int) -> str:
    """
    Gera token assinado contendo id e iat.
    """
    payload = {"id": int(pagamento_id), "iat": int(time.time())}
    return signing.dumps(payload, salt=SIGNING_SALT)


def loads_recibo_token(token: str, max_age: int = None) -> dict:
    """
    Valida e desserializa token. Levanta signing.BadSignature ou signing.SignatureExpired.
    """
    max_age = max_age if max_age is not None else TOKEN_MAX_AGE
    return signing.loads(token, salt=SIGNING_SALT, max_age=max_age)


def make_recibo_link(request, pagamento_id: int) -> str:
    """
    Retorna URL absoluta para a view pública do recibo por token.
    """
    token = make_recibo_token(pagamento_id)
    path = reverse("pagina_recibo_por_token", args=[token])
    return request.build_absolute_uri(path)