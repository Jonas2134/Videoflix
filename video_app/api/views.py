import os

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, Http404
from django.conf import settings

from .serializers import VideoSerializer
from video_app.models import Movie


class VideoListView(generics.GenericAPIView):
    """
    API view for listing videos.

    Attributes:
        queryset (QuerySet): The queryset for retrieving video objects.
        serializer_class (Serializer): The serializer class for validating and serializing video data.
        permission_classes (list): The permission classes for the view.
    """
    queryset = Movie.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Handle GET request for listing videos.

        1. Retrieve the list of videos from the database.
        2. Serialize the video data.
        3. Return the serialized data in the response.

        Returns:
            Response: The response containing the list of videos.
        """
        videos = self.get_queryset()
        serializer = self.get_serializer(videos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


def video_hls(request, movie_id, resolution, segment=None):
    """
    Handle HLS video streaming.

    1. Validate the request parameters.
    2. If segment is None, set it to 'index.m3u8'.
    3. Construct the file path for the video segment.
    4. If the file exists, return it as a FileResponse.
    5. If not, raise a 404 error.

    Returns:
        FileResponse: The response containing the video segment or an error.
    """
    if segment is None:
        segment = 'index.m3u8'
        
    file_path = os.path.join(settings.MEDIA_ROOT, f"videos/hls/{movie_id}/{resolution}/{segment}")
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'))
    else:
        raise Http404("File not found")
