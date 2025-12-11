from django.db import models
from django.conf import settings


class Reaction(models.Model):
    class Type(models.TextChoices):
        LIKE = "like", "Like"
        DISLIKE = "dislike", "Dislike"

    article = models.ForeignKey("articles.Article", on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reactions")
    type = models.CharField(max_length=10, choices=Type.choices)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reactions"
        unique_together = ("article", "user")

    def __str__(self):
        return f"{self.user.email} - {self.type} - {self.article.title}"