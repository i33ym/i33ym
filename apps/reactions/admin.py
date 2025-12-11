from django.contrib import admin
from .models import Reaction


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ("user", "article", "type", "is_anonymous", "created_at")
    list_filter = ("type", "is_anonymous", "created_at")
    search_fields = ("user__email", "article__title")
    raw_id_fields = ("user", "article")