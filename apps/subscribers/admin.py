from django.contrib import admin
from .models import Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "is_confirmed", "subscribed_at")
    list_filter = ("is_confirmed", "tags", "subscribed_at")
    search_fields = ("email",)
    filter_horizontal = ("tags",)
    readonly_fields = ("token",)