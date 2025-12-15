from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from .models import Tag, Article


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "author", "published_at", "created_at")
    list_filter = ("status", "tags", "created_at")
    search_fields = ("title", "excerpt", "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    date_hierarchy = "created_at"
    actions = ["notify_subscribers"]

    fieldsets = (
        (None, {"fields": ("title", "slug", "excerpt", "content")}),
        ("Categorization", {"fields": ("tags",)}),
        ("Publishing", {"fields": ("status", "published_at")}),
    )

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        if obj.status == Article.Status.PUBLISHED and not obj.published_at:
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)

    @admin.action(description="Notify subscribers about selected articles")
    def notify_subscribers(self, request, queryset):
        from apps.subscribers.emails import notify_subscribers_new_article

        for article in queryset.filter(status=Article.Status.PUBLISHED):
            notify_subscribers_new_article(article)

        messages.success(request, f"Notification sent for {queryset.count()} article(s)")