from django.db import models

# Create your models here.

class Movie(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='movies')
    video_file = models.FileField(upload_to='videos/')

    def __str__(self):
        return self.title


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
