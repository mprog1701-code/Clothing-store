from django.core.management.base import BaseCommand
from core.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        username = 'owner'
        email = 'owner@clothingstore.iq'
        password = '25802580'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'role': 'store_admin',
                'phone': '07700000000',
                'city': 'Baghdad',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        
        if not user.email:
            user.email = email
        if not user.phone:
            user.phone = '07700000000'
        if not user.city:
            user.city = 'Baghdad'
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        
        self.stdout.write(f'✓ Password updated for user: {user.username}')
        
        if created:
            self.stdout.write('✓ Owner created successfully')
        else:
            self.stdout.write('✓ Owner updated (password reset)')
