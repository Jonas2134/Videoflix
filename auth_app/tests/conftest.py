import pytest
import redis
from django.contrib.auth.models import User
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
def user(db):
    user = User.objects.create_user(
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
