import os
import subprocess
from django.conf import settings
from django.core.files import File
from django_rq import job

from .models import Movie


def convert_to_mp4_resolutions(movie, input_file):
    mp4_resolutions = {
        "video_converted_360p": ("640:360", f"{movie.id}_360p.mp4"),
        "video_converted_480p": ("854:480", f"{movie.id}_480p.mp4"),
        "video_converted_720p": ("1280:720", f"{movie.id}_720p.mp4"),
        "video_converted_1080p": ("1920:1080", f"{movie.id}_1080p.mp4"),
    }
    for field, (size, filename) in mp4_resolutions.items():
        output_path = os.path.join(settings.MEDIA_ROOT, f"videos/{field.replace('video_converted_', '')}/", filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cmd = [
            "ffmpeg",
            "-i", input_file,
            "-vf", f"scale={size}",
            "-c:a", "aac",
            "-y",
            output_path,
        ]
        subprocess.run(cmd, check=True)
        with open(output_path, "rb") as f:
            getattr(movie, field).save(filename, File(f), save=False)


def convert_to_hls(movie, input_file):
    hls_dir = os.path.join(settings.MEDIA_ROOT, f"videos/hls/{movie.id}")
    os.makedirs(hls_dir, exist_ok=True)
    hls_master = os.path.join(hls_dir, "master.m3u8")
    cmd_hls = [
        "ffmpeg",
        "-i", input_file,
        "-map", "0:v:0", "-map", "0:a:0?",
        "-c:v", "h264", "-c:a", "aac", "-strict", "-2",
        "-f", "hls",
        "-hls_time", "10",
        "-hls_list_size", "0",
        "-hls_segment_filename", os.path.join(hls_dir, "segment_%03d.ts"),
        hls_master,
    ]
    try:
        subprocess.run(cmd_hls, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print("ffmpeg HLS error:", e.stderr)
        raise
    with open(hls_master, "rb") as f:
        movie.hls_playlist.save(f"{movie.id}_master.m3u8", File(f), save=False)


@job
def convert_movie_task(movie_id):
    movie = Movie.objects.get(id=movie_id)
    input_file = movie.video_file.path
    convert_to_mp4_resolutions(movie, input_file)
    convert_to_hls(movie, input_file)
    movie.save()


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
