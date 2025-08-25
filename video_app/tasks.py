import os
import subprocess
from django.conf import settings
from django.core.files import File
from django_rq import job

from .models import Movie


@job
def generate_thumbnail(movie_id):
    movie = Movie.objects.get(id=movie_id)
    if not movie.thumbnail and movie.video_file:
        thumb_dir = os.path.join(settings.MEDIA_ROOT, "thumbnails")
        os.makedirs(thumb_dir, exist_ok=True)
        thumb_path = os.path.join(thumb_dir, f"{movie.id}_thumb.jpg")
        subprocess.run([
            "ffmpeg", "-i", movie.video_file.path,
            "-ss", "00:00:01.000", "-vframes", "1",
            "-q:v", "2", thumb_path
        ], check=True)
        with open(thumb_path, "rb") as f:
            movie.thumbnail.save(f"{movie.id}_thumb.jpg", File(f), save=True)


def convert_to_hls(movie, input_file):
    hls_resolutions = {
        "360p": "640:360",
        "480p": "854:480",
        "720p": "1280:720",
        "1080p": "1920:1080",
    }
    for res, size in hls_resolutions.items():
        hls_dir = os.path.join(settings.MEDIA_ROOT, f"videos/hls/{movie.id}/{res}")
        os.makedirs(hls_dir, exist_ok=True)
        hls_index = os.path.join(hls_dir, "index.m3u8")

        cmd = [
            "ffmpeg",
            "-i", input_file,
            "-vf", f"scale={size}",
            "-c:v", "h264", "-c:a", "aac", "-strict", "-2",
            "-f", "hls",
            "-hls_time", "10",
            "-hls_list_size", "0",
            "-hls_segment_filename", os.path.join(hls_dir, "segment_%03d.ts"),
            hls_index,
        ]

        subprocess.run(cmd, check=True)


@job
def convert_movie_task(movie_id):
    movie = Movie.objects.get(id=movie_id)
    input_file = movie.video_file.path
    convert_to_hls(movie, input_file)
    movie.save()
