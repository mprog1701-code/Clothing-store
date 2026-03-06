#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings_railway')
django.setup()

from django.contrib.auth import get_user_model, authenticate
User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'owner')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'owner@clothingstore.iq')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '25802580')

print("=== CREATE OR RESET OWNER USER ===")

user, _ = User.objects.get_or_create(
    username=username,
    defaults={
        'email': email,
        'role': 'store_admin',
        'phone': '07700000000',
        'city': 'Baghdad',
        'is_staff': True,
        'is_superuser': True,
        'is_active': True,
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

login_ok = authenticate(username=username, password=password) is not None
print(f"Username: {username}")
print(f"Password set from env/fallback: {password}")
print(f"Login test: {login_ok}")
print("=== SUPERUSER CREATION COMPLETED ===")
