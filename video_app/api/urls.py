from django.urls import path

from .views import VideoListView, video_hls

urlpatterns = [
    path('video/', VideoListView.as_view(), name='video-list'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', video_hls),
    path('video/<int:movie_id>/<str:resolution>/<str:segment>', video_hls),
]
