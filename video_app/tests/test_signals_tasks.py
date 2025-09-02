import os
import json
import pytest

from unittest import mock

from video_app.models import Movie
from video_app.signals import movie_post_save, delete_movie_files
from video_app import tasks


@pytest.mark.django_db
def test_movie_post_save_triggers_tasks(movie):
    with mock.patch("video_app.signals.generate_thumbnail.delay") as mock_thumb, \
         mock.patch("video_app.signals.convert_movie_task.delay") as mock_convert, \
         mock.patch("django.db.transaction.on_commit") as mock_tx:

        mock_tx.side_effect = lambda func: func()
        movie_post_save(Movie, movie, created=True)

    assert mock_thumb.called
    assert mock_convert.called


@pytest.mark.django_db
def test_delete_movie_files(tmp_path, movie):
    hls_dir = tmp_path / f"videos/hls/{movie.id}/720p"
    hls_dir.mkdir(parents=True)
    (hls_dir / "index.m3u8").write_text("dummy")

    thumb_dir = tmp_path / "thumbnails"
    thumb_dir.mkdir()
    thumb_file = thumb_dir / f"{movie.id}_thumb.jpg"
    thumb_file.write_bytes(b"thumb")

    with mock.patch("video_app.signals.settings.MEDIA_ROOT", tmp_path):
        delete_movie_files(Movie, movie)

    assert not os.path.exists(movie.video_file.path)
    assert not hls_dir.exists()
    assert not thumb_file.exists()


@pytest.mark.django_db
def test_generate_thumbnail_runs_ffmpeg(movie):
    movie.video_file = mock.Mock()
    movie.video_file.path = "/fake/path.mp4"
    movie.thumbnail = None

    with mock.patch("subprocess.run") as mock_run, \
         mock.patch("builtins.open", mock.mock_open(read_data=b"thumbdata")), \
         mock.patch("django.db.models.fields.files.ImageFieldFile.save", autospec=True) as mock_save:

        mock_run.return_value = mock.Mock(returncode=0)
        tasks.generate_thumbnail(movie.id)

        assert mock_run.called
        assert mock_save.called


def test_has_audio_stream_true_false(movie_file):
    ffprobe_out = json.dumps({"streams": [{"codec_type": "audio"}]})
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(stdout=ffprobe_out)
        assert tasks.has_audio_stream(str(movie_file)) is True

    ffprobe_out = json.dumps({})
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(stdout=ffprobe_out)
        assert tasks.has_audio_stream(str(movie_file)) is False


@pytest.mark.django_db
def test_convert_to_hls_calls_ffmpeg(movie):
    with mock.patch("video_app.tasks.has_audio_stream", return_value=True), \
         mock.patch("subprocess.run") as mock_run:
        tasks.convert_to_hls(movie, str(movie.video_file.path))

    assert mock_run.called
    args, _ = mock_run.call_args
    assert str(movie.video_file.path) in args[0]
    assert "-c:a" in args[0]


@pytest.mark.django_db
def test_convert_movie_task_runs(movie):
    with mock.patch("video_app.tasks.convert_to_hls") as mock_convert:
        tasks.convert_movie_task(movie.id)

    mock_convert.assert_called_once()
