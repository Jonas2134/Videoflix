import re
import pytest
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.core import mail


@pytest.mark.django_db
def test_register_view_creates_user(api_client, register_url):
    payload = {
        "email": "beispiel@test.com",
        "password": "pw12345",
        "confirmed_password": "pw12345"
    }
    response = api_client.post(register_url, payload, format='json')
    assert response.status_code == 201
    user = User.objects.get(email="beispiel@test.com")
    assert user.username == "beispieltest"


@pytest.mark.django_db
def test_register_view_handeles_username_conflict(api_client, register_url):
    User.objects.create_user(username="beispieltest", email="beispiel@test.com", password="pw12345")
    payload = {
        "email": "beispiel@test.de",
        "password": "pw12345",
        "confirmed_password": "pw12345"
    }
    response = api_client.post(register_url, payload, format='json')
    assert response.status_code == 201
    user = User.objects.get(email="beispiel@test.de")
    assert user.username.startswith("beispieltest")
    assert user.username != "beispieltest"


@pytest.mark.django_db
def test_register_sends_activation_email(api_client, register_url):
    payload = {
        "email": "activate_me@test.com",
        "password": "pw12345",
        "confirmed_password": "pw12345"
    }
    response = api_client.post(register_url, payload, format='json')
    assert response.status_code == 201
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert "activate_me@test.com" in email.to
    assert "/api/activate/" in email.body
    match = re.search(r'/api/activate/[\w\-]+/[\w\-]+/', email.body)
    assert match is not None


@pytest.mark.django_db
def test_activate_account_view(api_client, user, activate_url):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    url = activate_url(uidb64, token)
    response = api_client.get(url)
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_active is True


@pytest.mark.django_db
def test_activate_account_view_invalid(api_client, activate_url):
    url = activate_url('invalid', 'invalid')
    response = api_client.get(url)
    assert response.status_code == 400
    assert "error" in response.data


@pytest.mark.django_db
def test_login_view(api_client, user, login_url):
    payload = {
        "email": user.email,
        "password": "pw12345"
    }
    response = api_client.post(login_url, payload, format='json')
    assert response.status_code == 200
    assert "user" in response.data
    assert response.cookies.get('refresh_token')
    assert response.cookies.get('access_token')


@pytest.mark.django_db
def test_login_view_invalid(api_client, login_url):
    payload = {
        "email": "notfound@test.com",
        "password": "wrongpw"
    }
    response = api_client.post(login_url, payload, format='json')
    assert response.status_code == 401 or response.status_code == 400


@pytest.mark.django_db
def test_logout_view(api_client, user, login_url, logout_url):
    payload = {"email": user.email, "password": "pw12345"}
    login_response = api_client.post(login_url, payload, format='json')
    refresh_token = login_response.cookies.get('refresh_token').value
    api_client.cookies['refresh_token'] = refresh_token
    response = api_client.post(logout_url)
    assert response.status_code == 200
    assert response.data["detail"] == "Logout successful"


@pytest.mark.django_db
def test_logout_view_no_token(api_client, logout_url):
    response = api_client.post(logout_url)
    assert response.status_code == 400
    assert "Refresh token not found" in response.data["detail"]


@pytest.mark.django_db
def test_token_refresh_view(api_client, user, login_url, token_refresh_url):
    payload = {"email": user.email, "password": "pw12345"}
    login_response = api_client.post(login_url, payload, format='json')
    refresh_token = login_response.cookies.get('refresh_token').value
    api_client.cookies['refresh_token'] = refresh_token
    response = api_client.post(token_refresh_url)
    assert response.status_code == 200
    assert "access" in response.data


@pytest.mark.django_db
def test_token_refresh_view_no_token(api_client, token_refresh_url):
    response = api_client.post(token_refresh_url)
    assert response.status_code == 400
    assert "Refresh token not found" in response.data["detail"]


@pytest.mark.django_db
def test_password_reset_view(api_client, user, password_reset_url):
    payload = {"email": user.email}
    response = api_client.post(password_reset_url, payload, format='json')
    assert response.status_code == 200
    assert "reset" in mail.outbox[0].body or "password" in mail.outbox[0].body.lower()


@pytest.mark.django_db
def test_password_reset_view_invalid(api_client, password_reset_url):
    payload = {"email": "notfound@test.com"}
    response = api_client.post(password_reset_url, payload, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_password_confirm_view(api_client, user, password_confirm_url):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    url = password_confirm_url(uidb64, token)
    payload = {
        "new_password": "newsecurepw123",
        "confirm_password": "newsecurepw123"
    }
    response = api_client.post(url, payload, format='json')
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password("newsecurepw123")


@pytest.mark.django_db
def test_password_confirm_view_invalid_token(api_client, user, password_confirm_url):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    url = password_confirm_url(uidb64, 'invalid')
    payload = {
        "new_password": "newsecurepw123",
        "confirm_password": "newsecurepw123"
    }
    response = api_client.post(url, payload, format='json')
    assert response.status_code == 400
    assert "Invalid token" in response.data["detail"]


@pytest.mark.django_db
def test_password_confirm_view_invalid_user(api_client, password_confirm_url):
    url = password_confirm_url('invalid', 'invalid')
    payload = {"new_password": "newsecurepw123"}
    response = api_client.post(url, payload, format='json')
    assert response.status_code == 400
    assert "Invalid user" in response.data["detail"]
