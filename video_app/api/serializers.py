from rest_framework import serializers

from video_app.models import Movie

class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for video objects.
    This serializer validates and serializes video data for API responses.

    Fields:
        id (int): The unique identifier for the video.
        created_at (datetime): The timestamp when the video was created.
        title (str): The title of the video.
        description (str): A brief description of the video.
        thumbnail_url (str): The URL of the video's thumbnail image.
        category (str): The name of the category the video belongs to.
    """
    thumbnail_url = serializers.SerializerMethodField()
    category = serializers.CharField(source='category.name')

    class Meta:
        """
        Meta class for video serializer.

        Attributes:
            model (Model): The model class associated with the serializer.
            fields (tuple): The fields to include in the serialized output.
        """
        model = Movie
        fields = ('id', 'created_at', 'title', 'description', 'thumbnail_url', 'category')

    def get_thumbnail_url(self, obj):
        """
        Get the absolute URL for the video's thumbnail image.

        Args:
            obj (Movie): The movie object being serialized.

        Returns:
            str: The absolute URL of the thumbnail image, or None if not available.
        """
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None
