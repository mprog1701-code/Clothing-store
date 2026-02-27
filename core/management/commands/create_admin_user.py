from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create a superuser 'admin' with placeholder email and password"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = "admin"
        email = "EMAIL_HERE"
        password = "Admin12345!"
        defaults = {"email": email}
        # Optional phone for custom user model
        if hasattr(User, "phone"):
            defaults["phone"] = "07900000001"
        user, created = User.objects.get_or_create(username=username, defaults=defaults)
        if created:
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created superuser '{username}' with email {email}"))
        else:
            self.stdout.write(self.style.WARNING(f"User '{username}' already exists; updating email and flags"))
            user.email = email
            user.is_superuser = True
            user.is_staff = True
            if hasattr(User, "phone"):
                user.phone = user.phone or "07900000001"
            user.save()
            self.stdout.write(self.style.SUCCESS("Updated user"))
