from django.db import models


class IngestionLog(models.Model):
    source = models.CharField(max_length=255)
    chunks_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source} ({self.chunks_count} chunks)"