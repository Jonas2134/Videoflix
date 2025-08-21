import os
import subprocess
from django.conf import settings
from django.core.files import File

from .models import Movie


def convert_movie_task(movie_id):
    movie = Movie.objects.get(id=movie_id)
    input_file = movie.video_file.path

    mp4_resolutions = {
        "video_converted_360p": ("640:360", f"{movie_id}_360p.mp4"),
        "video_converted_480p": ("854:480", f"{movie_id}_480p.mp4"),
        "video_converted_720p": ("1280:720", f"{movie_id}_720p.mp4"),
        "video_converted_1080p": ("1920:1080", f"{movie_id}_1080p.mp4"),
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

    hls_dir = os.path.join(settings.MEDIA_ROOT, f"videos/hls/{movie_id}")
    os.makedirs(hls_dir, exist_ok=True)
    hls_master = os.path.join(hls_dir, "master.m3u8")

    cmd_hls = [
        "ffmpeg",
        "-i", input_file,
        "-map", "0:v:0", "-map", "0:a:0",
        "-c:v", "h264", "-c:a", "aac", "-strict", "-2",
        "-f", "hls",
        "-hls_time", "10",
        "-hls_list_size", "0",
        "-hls_segment_filename", os.path.join(hls_dir, "segment_%03d.ts"),
        hls_master,
    ]
    subprocess.run(cmd_hls, check=True)

    with open(hls_master, "rb") as f:
        movie.hls_playlist.save(f"{movie_id}_master.m3u8", File(f), save=False)

    movie.save()
