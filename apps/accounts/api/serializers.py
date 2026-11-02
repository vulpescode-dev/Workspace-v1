from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.models.auth import BIO_MAX_LENGTH
from apps.accounts.selectors.profile import avatar_url, department_name, initials


class ProfileSerializer(serializers.ModelSerializer):
    """Perfil dentro de la intranet. ``posts_count`` llega por contexto."""

    name = serializers.CharField(source="display_name", read_only=True)
    initials = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    is_me = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    follow = serializers.SerializerMethodField()
    birthday = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    department_id = serializers.IntegerField(read_only=True)
    manager = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "name", "first_name", "initials", "email", "job_title", "department", "department_id", "manager",
            "bio", "avatar_url", "date_joined", "birthday", "is_me", "posts_count", "follow",
        ]
        read_only_fields = fields

    def get_initials(self, user) -> str:
        return initials(user.display_name)

    def get_avatar_url(self, user) -> str:
        return avatar_url(user)

    def get_department(self, user) -> str:
        return department_name(user)

    def get_manager(self, user) -> dict | None:
        """Jefe directo (forma corta) si está activo; si no, ``None``."""
        manager = user.manager
        if manager is None or not manager.is_active:
            return None
        return AuthorSerializer(manager).data

    def get_birthday(self, user) -> dict | None:
        """Solo día y mes (``{"day": 18, "month": 11}``): el año —la edad— nunca sale del servidor."""
        if not user.birth_date:
            return None
        return {"day": user.birth_date.day, "month": user.birth_date.month}

    def get_is_me(self, user) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.pk == user.pk)

    def get_posts_count(self, user) -> int:
        return self.context.get("posts_count", 0)

    def get_follow(self, user) -> dict:
        """``followers_count``, ``following_count``, ``is_following`` (yo lo sigo), ``follows_me`` (me sigue)."""
        return self.context.get("follow", {})


class BioInputSerializer(serializers.Serializer):
    # El límite real (280) lo aplica services.profile después de normalizar espacios.
    bio = serializers.CharField(max_length=BIO_MAX_LENGTH * 2, allow_blank=True, trim_whitespace=True)


class DirectoryPersonSerializer(serializers.ModelSerializer):
    """Tarjeta del directorio. ``followed_ids`` y ``viewer_id`` llegan por contexto."""

    name = serializers.CharField(source="display_name", read_only=True)
    initials = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    is_me = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    department_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "name", "initials", "avatar_url", "email", "job_title", "department", "department_id", "is_me",
            "is_following",
        ]
        read_only_fields = fields

    def get_department(self, user) -> str:
        return department_name(user)

    def get_initials(self, user) -> str:
        return initials(user.display_name)

    def get_avatar_url(self, user) -> str:
        return avatar_url(user)

    def get_is_me(self, user) -> bool:
        return user.pk == self.context.get("viewer_id")

    def get_is_following(self, user) -> bool:
        return user.pk in self.context.get("followed_ids", set())


class BirthdaySerializer(serializers.Serializer):
    """Cumpleaños próximo. Sin año ni edad: solo día y mes de la próxima fecha."""

    id = serializers.IntegerField(source="user.pk")
    name = serializers.CharField(source="user.display_name")
    initials = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    job_title = serializers.CharField(source="user.job_title")
    day = serializers.IntegerField(source="next_date.day")
    month = serializers.IntegerField(source="next_date.month")
    days_until = serializers.IntegerField()
    is_today = serializers.SerializerMethodField()

    def get_initials(self, birthday) -> str:
        return initials(birthday.user.display_name)

    def get_avatar_url(self, birthday) -> str:
        return avatar_url(birthday.user)

    def get_is_today(self, birthday) -> bool:
        return birthday.days_until == 0


class AuthorSerializer(serializers.Serializer):
    """Persona en forma corta (autor de un artículo, quien vende…): id, nombre, iniciales y foto."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.SerializerMethodField()
    initials = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    def get_name(self, user) -> str:
        return user.get_full_name() or user.username

    def get_initials(self, user) -> str:
        return initials(self.get_name(user))

    def get_avatar_url(self, user) -> str:
        return avatar_url(user)
