import os
import shutil
import glob

from django.db.models.signals import post_save, post_delete
from django.db import transaction
from django.dispatch import receiver
from django.conf import settings

from .models import Movie
from .tasks import convert_movie_task, generate_thumbnail


@receiver(post_save, sender=Movie)
def movie_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for post-save actions on Movie instances.
    If a new Movie instance is not created, the function returns immediately.
    If a new Movie instance is created, has a title, description, category and has an associated video file.
    It triggers asynchronous tasks for generating a thumbnail and converting the video.
    """
    if not created:
        return

    if created and instance.title and instance.description and instance.category_id and instance.video_file:
        transaction.on_commit(lambda: generate_thumbnail.delay(instance.id))
        transaction.on_commit(lambda: convert_movie_task.delay(instance.id))


@receiver(post_delete, sender=Movie)
def delete_movie_files(sender, instance, **kwargs):
    """
    Signal handler for post-delete actions on Movie instances.
    It removes the associated video file and HLS segments from the filesystem
    and delete the thumbnail images.
    """
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)

    hls_base_dir = os.path.join(settings.MEDIA_ROOT, f'videos/hls/{instance.id}')
    if os.path.isdir(hls_base_dir):
        shutil.rmtree(hls_base_dir)

    thumb_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
    pattern = os.path.join(thumb_dir, f"{instance.id}_thumb*.jpg")
    for thumb_file in glob.glob(pattern):
        if os.path.isfile(thumb_file):
            os.remove(thumb_file)
