import pytest
from unittest import mock

from video_app.models import Movie

@pytest.mark.django_db
def test_video_integration(auth_client, user, category, movie_file):
    with mock.patch("video_app.signals.generate_thumbnail.delay") as mock_thumb, \
         mock.patch("video_app.signals.convert_movie_task.delay") as mock_convert, \
         mock.patch("django.db.transaction.on_commit", side_effect=lambda func: func()):

        movie = Movie.objects.create(
            title="Integration Test Movie",
            description="Integration test",
            category=category,
            video_file=str(movie_file)
        )

        assert mock_thumb.called
        assert mock_convert.called

        response = auth_client.get("/api/video/", format="json")
        assert response.status_code == 200
        assert len(response.data) == 1
        video_data = response.data[0]
        assert video_data["title"] == "Integration Test Movie"
        assert video_data["description"] == "Integration test"
        assert video_data["category"] == category.name
        assert "thumbnail_url" in video_data
