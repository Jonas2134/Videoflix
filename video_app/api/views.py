import os
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import FileResponse, Http404
from django.conf import settings

from .serializers import VideoSerializer
from video_app.models import Movie


class VideoListView(generics.GenericAPIView):
    queryset = Movie.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        videos = self.get_queryset()
        serializer = self.get_serializer(videos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


def video_hls(request, movie_id, resolution, segment=None):
    if segment is None:
        segment = 'index.m3u8'
        
    file_path = os.path.join(settings.MEDIA_ROOT, f"videos/hls/{movie_id}/{resolution}/{segment}")
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'))
    else:
        raise Http404("File not found")
