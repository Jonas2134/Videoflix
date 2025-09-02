import pytest
import os

from unittest import mock

from django.conf import settings
from django.http import Http404, FileResponse

from video_app.api.views import video_hls
from video_app.models import Movie


@pytest.mark.django_db
def test_video_list_view_authenticated(auth_client, movie):
    response = auth_client.get('/api/video/', format='json')
    assert response.status_code == 200
    assert response.data[0]['title'] == 'Test Movie'


@pytest.mark.django_db
def test_video_list_view_unauthenticated(api_client, movie):
    response = api_client.get('/api/video/', format='json')
    assert response.status_code == 401


@pytest.mark.django_db
def test_video_list_view_multiple_movies(auth_client, user, movie, category):
    Movie.objects.create(title='Another Movie', description='desc', video_file='test2.mp4', category=category)

    response = auth_client.get('/api/video/', format='json')

    assert response.status_code == 200
    assert len(response.data) == 2


def test_video_hls_file_exists(rf):
    request = rf.get('/fake-url/')
    movie_id = 1
    resolution = '720p'
    segment = 'test.ts'

    with mock.patch('os.path.exists', return_value=True), \
         mock.patch('builtins.open', mock.mock_open(read_data=b'data')) as m_open:
        response = video_hls(request, movie_id, resolution, segment)
        assert isinstance(response, FileResponse)
        m_open.assert_called_once()


def test_video_hls_file_not_found(rf):
    request = rf.get('/fake-url/')
    movie_id = 1
    resolution = '720p'
    segment = 'test.ts'

    with mock.patch('os.path.exists', return_value=False):
        with pytest.raises(Http404):
            video_hls(request, movie_id, resolution, segment)


def test_video_hls_correct_path(rf):
    request = rf.get('/fake-url/')
    movie_id, resolution, segment = 1, "720p", "test.ts"
    expected_path = os.path.join(settings.MEDIA_ROOT, f"videos/hls/{movie_id}/{resolution}/{segment}")

    with mock.patch('os.path.exists', return_value=True) as m_exists, \
         mock.patch('builtins.open', mock.mock_open(read_data=b'data')):
        response = video_hls(request, movie_id, resolution, segment)
        assert isinstance(response, FileResponse)
        m_exists.assert_called_once_with(expected_path)


def test_video_hls_default_segment(rf):
    request = rf.get('/fake-url/')
    movie_id = 1
    resolution = '720p'

    with mock.patch('os.path.exists', return_value=True), \
         mock.patch('builtins.open', mock.mock_open(read_data=b'data')) as m_open:
        response = video_hls(request, movie_id, resolution)
        assert isinstance(response, FileResponse)
        m_open.assert_called_once()
