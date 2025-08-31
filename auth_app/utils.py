from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse


def build_link(request, user, url_path):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    current_site = get_current_site(request)
    link = f"http://{current_site.domain}{reverse(url_path, kwargs={'uidb64': uid, 'token': token})}"
    return link, token
