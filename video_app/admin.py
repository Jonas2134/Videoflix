from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Movie, Category

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for managing video categories.
    """
    list_display = ('name',)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    """
    Admin interface for managing video movies.
    It includes validation to ensure that title, description, category, and video_file are provided before saving.
    """
    list_display = ('title', 'category', 'created_at')
    readonly_fields = ('hls_master_playlist', )

    def save_model(self, request, obj, form, change):
        if not obj.title:
            raise ValidationError('Title cannot be empty.')
        if not obj.description:
            raise ValidationError('Description cannot be empty.')
        if not obj.category_id:
            raise ValidationError('Category must be set.')
        if not obj.video_file:
            raise ValidationError('Video file must be uploaded.')
        super().save_model(request, obj, form, change)
