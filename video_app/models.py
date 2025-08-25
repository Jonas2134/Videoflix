from django.db import models

# Create your models here.

class Movie(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='movies')

    video_file = models.FileField(upload_to='videos/originals/')

    video_converted_360p = models.FileField(upload_to='videos/360p/', null=True, blank=True)
    video_converted_480p = models.FileField(upload_to='videos/480p/', null=True, blank=True)
    video_converted_720p = models.FileField(upload_to='videos/720p/', null=True, blank=True)
    video_converted_1080p = models.FileField(upload_to='videos/1080p/', null=True, blank=True)

    hls_playlist = models.FileField(upload_to='videos/hls/', null=True, blank=True)

    def __str__(self):
        return self.title


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
