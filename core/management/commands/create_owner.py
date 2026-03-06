from django.core.management.base import BaseCommand
from core.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username='owner',
            defaults={
                'email': 'owner@clothingstore.iq',
                'role': 'store_admin',
                'phone': '07700000000',
                'city': 'Baghdad',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        
        user.set_password('Owner@2026!Iraq')
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        
        self.stdout.write(f'✓ Password updated for user: {user.username}')
        
        if created:
            self.stdout.write('✓ Owner created successfully')
        else:
            self.stdout.write('✓ Owner updated (password reset)')
