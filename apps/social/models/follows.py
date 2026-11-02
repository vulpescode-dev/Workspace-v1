from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Follow(models.Model):
    """«``follower`` sigue a ``following``». Inmediato, sin solicitud (decisión del proyecto).

    Seguir a alguien permite ver sus publicaciones de audiencia «Solo seguidores».
    """

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following_set", verbose_name="seguidor"
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers_set", verbose_name="sigue a"
    )
    created_at = models.DateTimeField("desde", auto_now_add=True)

    class Meta:
        verbose_name = "seguimiento"
        verbose_name_plural = "seguimientos"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="uniq_follow"),
            models.CheckConstraint(condition=~Q(follower=F("following")), name="no_self_follow"),
        ]
        indexes = [models.Index(fields=["following", "-created_at"], name="follow_following_idx")]

    def __str__(self) -> str:
        return f"{self.follower} → {self.following}"
