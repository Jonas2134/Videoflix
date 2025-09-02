from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    """
    Configuration class for the video application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video_app'

    def ready(self):
        """
        Signal registration for the video application.
        """
        import video_app.signals
