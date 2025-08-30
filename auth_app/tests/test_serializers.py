import pytest
from django.contrib.auth import get_user_model
from auth_app.api.serializers import (
    RegisterSerializer,
    LoginSerializer,
    PasswordResetSerializer,
    PasswordConfirmSerializer,
)

User = get_user_model()


@pytest.mark.django_db
def test_register_serializer_valid():
    data = {
        "email": "testuser@example.com",
        "password": "pw12345",
        "confirmed_password": "pw12345"
    }
    serializer = RegisterSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    user = serializer.save()
    assert user.email == "testuser@example.com"
    assert user.username.startswith("testuser")
    assert not user.is_active
    assert user.check_password("pw12345")


@pytest.mark.django_db
def test_register_serializer_password_mismatch():
    data = {
        "email": "testuser2@example.com",
        "password": "pw12345",
        "confirmed_password": "wrongpw"
    }
    serializer = RegisterSerializer(data=data)
    assert not serializer.is_valid()
    assert "confirmed_password" in serializer.errors


@pytest.mark.django_db
def test_register_serializer_duplicate_email():
    User.objects.create_user(username="dupuser", email="dup@example.com", password="pw12345")
    data = {
        "email": "dup@example.com",
        "password": "pw12345",
        "confirmed_password": "pw12345"
    }
    serializer = RegisterSerializer(data=data)
    assert not serializer.is_valid()
    assert "email" in serializer.errors


@pytest.mark.django_db
def test_login_serializer_valid():
    User.objects.create_user(username="loginuser", email="login@example.com", password="pw12345")
    data = {
        "email": "login@example.com",
        "password": "pw12345"
    }
    serializer = LoginSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    result = serializer.validate(data)
    assert result["user"]["username"] == "loginuser"
    assert "access" in result and "refresh" in result


@pytest.mark.django_db
def test_login_serializer_wrong_password():
    User.objects.create_user(username="loginuser2", email="login2@example.com", password="pw12345")
    data = {
        "email": "login2@example.com",
        "password": "wrongpw"
    }
    serializer = LoginSerializer(data=data)
    with pytest.raises(Exception):
        serializer.validate(data)


@pytest.mark.django_db
def test_login_serializer_nonexistent_email():
    data = {
        "email": "doesnotexist@example.com",
        "password": "pw12345"
    }
    serializer = LoginSerializer(data=data)
    with pytest.raises(Exception):
        serializer.validate(data)


@pytest.mark.django_db
def test_password_reset_serializer_valid():
    User.objects.create_user(username="resetuser", email="reset@example.com", password="pw12345")
    data = {"email": "reset@example.com"}
    serializer = PasswordResetSerializer(data=data)
    assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
def test_password_reset_serializer_invalid():
    data = {"email": "notfound@example.com"}
    serializer = PasswordResetSerializer(data=data)
    assert not serializer.is_valid()
    assert "email" in serializer.errors


def test_password_confirm_serializer_valid():
    data = {
        "new_password": "pw12345",
        "confirm_password": "pw12345"
    }
    serializer = PasswordConfirmSerializer(data=data, context={"user": None})
    assert serializer.is_valid(), serializer.errors


def test_password_confirm_serializer_mismatch():
    data = {
        "new_password": "pw12345",
        "confirm_password": "wrongpw"
    }
    serializer = PasswordConfirmSerializer(data=data, context={"user": None})
    assert not serializer.is_valid()
    assert "confirm_password" in serializer.errors


@pytest.mark.django_db
def test_password_confirm_serializer_same_as_old():
    user = User.objects.create_user(username="oldpwuser", email="oldpw@example.com", password="pw12345")
    data = {
        "new_password": "pw12345",
        "confirm_password": "pw12345"
    }
    serializer = PasswordConfirmSerializer(data=data, context={"user": user})
    assert not serializer.is_valid()
    assert "new_password" in serializer.errors
