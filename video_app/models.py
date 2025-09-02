import os

from django.db import models
from django.conf import settings

# Create your models here.

class Movie(models.Model):
    """
    Model representing a video movie.

    Attributes:
        created_at (datetime): The timestamp when the movie was created.
        title (str): The title of the movie.
        description (str): A brief description of the movie.
        thumbnail (ImageField): The thumbnail image for the movie.
        category (ForeignKey): The category the movie belongs to.
        video_file (FileField): The original video file.
        hls_master_playlist (FileField): The HLS master playlist file.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='movies')

    video_file = models.FileField(upload_to='videos/originals/')

    hls_master_playlist = models.FileField(upload_to='videos/hls_master/', null=True, blank=True)

    def get_hls_index_path(self, resolution):
        """
        Get the HLS index path for a specific resolution.

        Args:
            resolution (str): The resolution for which to get the HLS index path.

        Returns:
            str: The HLS index path for the specified resolution.
        """
        return os.path.join(settings.MEDIA_URL, f"videos/hls/{self.id}/{resolution}/index.m3u8")

    def __str__(self):
        """
        String representation of the movie.
        """
        return self.title


class Category(models.Model):
    """
    Model representing a video category.

    Attributes:
        name (str): The name of the category.
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        """
        String representation of the category.
        """
        return self.name
