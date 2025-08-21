from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Movie
from .tasks import convert_movie_task


@receiver(post_save, sender=Movie)
def movie_post_save(sender, instance, created, **kwargs):
    if created and instance.video_file:
        convert_movie_task.delay(instance.id)
