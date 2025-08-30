import re
import pytest
from django.contrib.auth.models import User
from django.core import mail

@pytest.mark.django_db
def test_full_registration_activation_login_flow(api_client, register_url, activate_url, login_url):
    payload = {
        "email": "integration@test.com",
        "password": "pw12345",
        "confirmed_password": "pw12345"
    }
    response = api_client.post(register_url, payload, format='json')
    assert response.status_code == 201
    user = User.objects.get(email="integration@test.com")
    assert not user.is_active

    assert len(mail.outbox) == 1
    email_body = mail.outbox[0].body
    match = re.search(r'/api/activate/([\w\-]+)/([\w\-]+)/', email_body)
    assert match is not None
    uidb64, token = match.groups()

    url = activate_url(uidb64, token)
    response = api_client.get(url)
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_active

    payload = {
        "email": "integration@test.com",
        "password": "pw12345"
    }
    response = api_client.post(login_url, payload, format='json')
    assert response.status_code == 200
    assert "user" in response.data
    assert response.cookies.get('refresh_token')
    assert response.cookies.get('access_token')


@pytest.mark.django_db
def test_password_reset_and_confirm_flow(api_client, user, password_reset_url, password_confirm_url, login_url):
    payload = {"email": user.email}
    response = api_client.post(password_reset_url, payload, format='json')
    assert response.status_code == 200
    assert len(mail.outbox) == 1
    email_body = mail.outbox[0].body
    match = re.search(r'/api/password_confirm/([\w\-]+)/([\w\-]+)/', email_body)
    assert match is not None
    uidb64, token = match.groups()

    url = password_confirm_url(uidb64, token)
    payload = {
        "new_password": "integrationNewPW123",
        "confirm_password": "integrationNewPW123"
    }
    response = api_client.post(url, payload, format='json')
    assert response.status_code == 200

    payload = {
        "email": user.email,
        "password": "integrationNewPW123"
    }
    response = api_client.post(login_url, payload, format='json')
    assert response.status_code == 200
    assert "user" in response.data
