"""
Management command to create a default superuser.
Credentials are read from environment variables (.env) via python-decouple.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decouple import config


class Command(BaseCommand):
    help = "Create a default superuser from .env credentials"

    def handle(self, *args, **options):
        username = config("DJANGO_ADMIN_USERNAME", default="admin")
        email = config("DJANGO_ADMIN_EMAIL", default="admin@example.com")
        password = config("DJANGO_ADMIN_PASSWORD", default="changeme")

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f"✅ Superuser '{username}' created successfully."))
        else:
            self.stdout.write(f"⏭️  Superuser '{username}' already exists.")
