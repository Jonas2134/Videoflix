from django.contrib import admin

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
    """
    list_display = ('title', 'category', 'created_at')
    readonly_fields = ('hls_master_playlist', )
