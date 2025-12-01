#!/usr/bin/env python
"""
Management command to set or reset the owner password
Usage: python manage.py set_owner_password [new_password]
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from core.models import User

class Command(BaseCommand):
    help = 'Set or reset the owner password'

    def add_arguments(self, parser):
        parser.add_argument('password', type=str, help='New password for the owner')

    def handle(self, *args, **options):
        password = options['password']
        
        try:
            # Get or create the owner user
            user, created = User.objects.get_or_create(
                phone='0500000000',
                defaults={
                    'username': 'owner_admin',
                    'first_name': 'صاحب',
                    'last_name': 'المتجر',
                    'role': 'admin',
                    'owner_key': 'OWNER2025',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            
            # Set the password
            user.set_password(password)
            user.save()
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ تم إنشاء حساب المالك بنجاح!')
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'🔐 تم تعيين كلمة مرور المالك إلى: {password}')
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'📱 رقم الجوال: 0500000000')
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'🔑 مفتاح المالك: OWNER2025')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ خطأ: {str(e)}')
            )