#!/usr/bin/env python
import os
import sys
import django

# Use railway settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings_railway')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

print("Force updating superuser password...")
try:
    # Try to get existing user or create new one
    user, created = User.objects.get_or_create(
        username='owner',
        defaults={
            'email': 'owner@clothingstore.iq',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )
    
    # FORCE set password
    user.set_password('Owner2026Iraq')
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    
    if hasattr(user, 'role'):
        user.role = 'admin'
        
    user.save()

    print('✓ Password FORCE updated successfully!')
    print(f'User: {user.username}')
    print('Pass: Owner2026Iraq')
    
except Exception as e:
    print(f"Error updating password: {e}")
