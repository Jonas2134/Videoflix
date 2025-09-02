import pytest
import redis

from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def clear_redis():
    client = redis.Redis(host='redis', port=6379, db=0)
    client.flushdb()
    yield
    client.flushdb()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db, django_user_model):
    user = django_user_model.objects.create_user(
        username="existingtest",
        email="existing@test.com",
        password="pw12345",
        is_active=True
    )
    return user


@pytest.fixture
def auth_client(api_client, user):
    login_url = '/api/login/'
    response = api_client.post(login_url, {
        "email": user.email,
        "password": "pw12345"
    }, format='json')
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def register_url():
    return reverse('register')


@pytest.fixture
def activate_url():
    def _url(uidb64, token):
        return reverse('activate', kwargs={'uidb64': uidb64, 'token': token})
    return _url


@pytest.fixture
def login_url():
    return reverse('login')


@pytest.fixture
def logout_url():
    return reverse('logout')


@pytest.fixture
def token_refresh_url():
    return reverse('token_refresh')


@pytest.fixture
def password_reset_url():
    return reverse('password_reset')


@pytest.fixture
def password_confirm_url():
    def _url(uidb64, token):
        return reverse('password_confirm', kwargs={'uidb64': uidb64, 'token': token})
    return _url
