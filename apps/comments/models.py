from django.db import models
from django.conf import settings


class Comment(models.Model):
    article = models.ForeignKey("articles.Article", on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "comments"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.user.is_banned:
            self.is_approved = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} on {self.article.title}"