import os
import subprocess
import json

from django.conf import settings
from django.core.files import File
from django_rq import job

from .models import Movie


@job
def generate_thumbnail(movie_id):
    """
    Generate a thumbnail for the specified movie.
    This function uses ffmpeg to extract a frame from the video file and save it as a thumbnail image.
    This is a background task that can be queued for processing.

    Args:
        movie_id (int): The ID of the movie for which to generate a thumbnail.
    """
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


def has_audio_stream(input_file):
    """
    Check if input file has an audio stream using ffprobe.

    Args:
        input_file (str): The path to the input video file.

    Returns:
        bool: True if the input file has an audio stream, False otherwise.
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=codec_type",
        "-of", "json",
        input_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    return "streams" in info and len(info["streams"]) > 0


def convert_to_hls(movie, input_file):
    """
    Convert the specified movie to HLS format.
    This function generates HLS segments and playlists for multiple resolutions.
    The generated files are stored in the media directory.

    Args:
        movie (Movie): The movie instance to convert.
        input_file (str): The path to the input video file.
    """
    hls_resolutions = {
        "480p": "854:480",
        "720p": "1280:720",
        "1080p": "1920:1080",
    }

    audio_exists = has_audio_stream(input_file)

    for res, size in hls_resolutions.items():
        hls_dir = os.path.join(settings.MEDIA_ROOT, f"videos/hls/{movie.id}/{res}")
        os.makedirs(hls_dir, exist_ok=True)
        hls_index = os.path.join(hls_dir, "index.m3u8")

        cmd = [
            "ffmpeg",
            "-i", input_file,
            "-vf", f"scale={size}",
            "-c:v", "h264",
            "-f", "hls",
            "-hls_time", "10",
            "-hls_list_size", "0",
            "-hls_segment_filename", os.path.join(hls_dir, "segment_%03d.ts"),
            hls_index,
        ]

        if audio_exists:
            cmd.insert(cmd.index("-c:v", ) + 2, "-c:a")
            cmd.insert(cmd.index("-c:v", ) + 3, "aac")

        subprocess.run(cmd, check=True)


@job
def convert_movie_task(movie_id):
    """
    Convert the specified movie to HLS format.
    This is a background task that retrieves the movie instance and calls the conversion function.

    Args:
        movie_id (int): The ID of the movie to convert.
    """
    movie = Movie.objects.get(id=movie_id)
    input_file = movie.video_file.path
    convert_to_hls(movie, input_file)
    movie.save()
