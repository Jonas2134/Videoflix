import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
import re


@pytest.mark.django_db
def test_register_view_creates_user(api_client):
    url = reverse('register')
    payload = {
        "email": "beispiel@test.com",
        "password": "pw12345",
        "confirmed_password": "pw12345"
    }

    response = api_client.post(url, payload, format='json')

    assert response.status_code == 201
    user = User.objects.get(email="beispiel@test.com")
    assert user.username == "beispieltest"


@pytest.mark.django_db
def test_register_view_handeles_username_conflict(api_client):
    User.objects.create_user(username="beispieltest", email="beispiel@test.com", password="pw12345")

    url = reverse('register')
    payload = {
        "email": "beispiel@test.de",
        "password": "pw12345",
        "confirmed_password": "pw12345"
    }

    response = api_client.post(url, payload, format='json')

    assert response.status_code == 201
    user = User.objects.get(email="beispiel@test.de")

    assert user.username.startswith("beispieltest")
    assert user.username != "beispieltest"


@pytest.mark.django_db
def test_register_sends_activation_email(api_client):
    url = reverse('register')
    payload = {
        "email": "activate_me@test.com",
        "password": "pw12345",
        "confirmed_password": "pw12345"
    }

    response = api_client.post(url, payload, format='json')

    assert response.status_code == 201
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert "activate_me@test.com" in email.to
    assert "/api/activate/" in email.body
    match = re.search(r'/api/activate/[\w\-]+/[\w\-]+/', email.body)
    assert match is not None
