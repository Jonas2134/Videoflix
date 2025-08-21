from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Movie


@receiver(post_save, sender=Movie)
def movie_post_save(sender, instance, created, **kwargs):
    if created:
        print(f"New movie created: {instance.title}")
    else:
        print(f"Movie updated: {instance.title}")
