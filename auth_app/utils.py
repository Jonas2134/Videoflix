from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


def build_link(user, url_path):
    """Builds a URL link for user actions (e.g., account activation, password reset)."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = f"http://127.0.0.1:5500/{url_path}?uid={uid}&token={token}"
    return link, token
