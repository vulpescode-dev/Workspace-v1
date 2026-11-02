"""Liga ``User.department`` con ``org.Department``.

Va aparte de ``0001_initial`` porque las dos apps se apuntan entre sí (``Department.head`` es un usuario):
primero se crea el usuario, luego el departamento y al final este campo.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('org', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='members', to='org.department', verbose_name='departamento'),
        ),
    ]
