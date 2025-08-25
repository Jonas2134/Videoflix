import os
from django.db import models
from django.conf import settings

# Create your models here.

class Movie(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='movies')

    video_file = models.FileField(upload_to='videos/originals/')

    hls_master_playlist = models.FileField(upload_to='videos/hls_master/', null=True, blank=True)

    def get_hls_index_path(self, resolution):
        return os.path.join(settings.MEDIA_URL, f"videos/hls/{self.id}/{resolution}/index.m3u8")

    def __str__(self):
        return self.title


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
