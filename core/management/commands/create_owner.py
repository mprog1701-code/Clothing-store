from django.core.management.base import BaseCommand
from core.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        if not User.objects.filter(username='owner').exists():
            User.objects.create_superuser(
                username='owner',
                email='owner@clothingstore.iq',
                password='Owner@2026!Iraq',
                role='store_admin',  # Use a valid choice from ROLE_CHOICES if needed, or just rely on is_superuser
                phone='07700000000',
                city='Baghdad'
            )
            self.stdout.write('✓ Owner created')
        else:
            self.stdout.write('Owner already exists')
