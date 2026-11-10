from apps.catalogs.models import Emoji


def active_emojis():
    """Emojis que se ofrecen en el selector, en su orden."""
    return Emoji.objects.filter(is_active=True)


def get_active_emoji(code: str) -> Emoji | None:
    return active_emojis().filter(code=code).first()
