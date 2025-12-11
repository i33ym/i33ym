from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "article", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("user__email", "article__title", "content")
    list_editable = ("is_approved",)
    raw_id_fields = ("user", "article")