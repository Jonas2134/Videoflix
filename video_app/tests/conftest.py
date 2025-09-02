import pytest

from django.test import RequestFactory
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from video_app.models import Movie, Category


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def rf():
    return RequestFactory()


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
    access = AccessToken.for_user(user)
    api_client.cookies['access_token'] = str(access)
    return api_client


@pytest.fixture
def category(db):
    return Category.objects.create(name="Test Category")


@pytest.fixture
def movie_file(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path / "media"
    file_path = settings.MEDIA_ROOT / "video.mp4"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"dummy video content")
    return file_path


@pytest.fixture
def movie(user, category, movie_file):
    return Movie.objects.create(
        title='Test Movie',
        description='desc',
        video_file=str(movie_file),
        category=category
    )
