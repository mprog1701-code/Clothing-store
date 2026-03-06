#!/usr/bin/env python
import os
import sys
import django

# Use railway settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings_railway')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# حذف المستخدم القديم إذا وُجد
try:
    User.objects.filter(username='owner').delete()
except Exception as e:
    print(f"Warning: Could not delete user: {e}")

# إنشاء جديد
print("Creating superuser...")
try:
    user = User.objects.create_superuser(
        username='owner',
        email='owner@clothingstore.iq',
        password='Owner2026Iraq'
    )

    # إذا كان User model مخصص
    if hasattr(user, 'role'):
        user.role = 'admin'
        user.save()

    print('✓ Superuser created successfully!')
    print('Username: owner')
    print('Password: Owner2026Iraq')
except Exception as e:
    print(f"Error creating superuser: {e}")
