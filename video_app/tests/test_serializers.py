import pytest
from rest_framework.test import APIRequestFactory
from video_app.api.serializers import VideoSerializer
from video_app.models import Movie, Category


@pytest.mark.django_db
def test_video_serializer_with_thumbnail(user, tmp_path):
    factory = APIRequestFactory()
    request = factory.get("/api/videos/")

    category = Category.objects.create(name="Action")

    thumbnail_file = tmp_path / "thumb.jpg"
    thumbnail_file.write_bytes(b"dummydata")

    movie = Movie.objects.create(
        title="Test Movie",
        description="desc",
        video_file="test.mp4",
        category=category,
        thumbnail=str(thumbnail_file),
    )

    serializer = VideoSerializer(movie, context={"request": request})
    data = serializer.data

    assert data["id"] == movie.id
    assert data["title"] == "Test Movie"
    assert data["category"] == "Action"
    assert data["thumbnail_url"].startswith("http://testserver/")
    assert data["thumbnail_url"].endswith("thumb.jpg")


@pytest.mark.django_db
def test_video_serializer_without_thumbnail(user):
    factory = APIRequestFactory()
    request = factory.get("/api/videos/")

    category = Category.objects.create(name="Drama")

    movie = Movie.objects.create(
        title="No Thumbnail Movie",
        description="desc",
        video_file="test.mp4",
        category=category,
        thumbnail="",
    )

    serializer = VideoSerializer(movie, context={"request": request})
    data = serializer.data

    assert data["thumbnail_url"] is None
    assert data["category"] == "Drama"