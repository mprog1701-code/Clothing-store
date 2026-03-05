
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Creates an admin user non-interactively if it doesn't exist"

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

        if not User.objects.filter(username=username).exists():
            try:
                # Add required fields for custom User model
                extra_fields = {}
                if hasattr(User, 'phone'):
                    extra_fields['phone'] = '07900000000'  # Dummy phone for admin
                if hasattr(User, 'city'):
                    extra_fields['city'] = 'Baghdad'      # Dummy city for admin
                
                User.objects.create_superuser(username=username, email=email, password=password, **extra_fields)
                self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created!'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating superuser: {e}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" already exists.'))
