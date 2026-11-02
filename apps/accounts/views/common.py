from apps.accounts.selectors.profile import avatar_url, initials


def shell_context(request) -> dict:
    """Datos del usuario que necesita el layout (menú, «Compártenos tu día…»)."""
    user = request.user
    return {
        "display_name": user.first_name or user.username,
        "display_initials": initials(user.display_name),
        "display_avatar_url": avatar_url(user),
    }
