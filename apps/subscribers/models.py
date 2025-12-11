from django.db import models
import secrets


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    tags = models.ManyToManyField("articles.Tag", related_name="subscribers", blank=True)
    is_confirmed = models.BooleanField(default=False)
    token = models.CharField(max_length=64, unique=True, blank=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "subscribers"
        ordering = ["-subscribed_at"]

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email