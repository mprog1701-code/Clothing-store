#!/usr/bin/env python
import os
import sys
import django

# Use railway settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings_railway')
django.setup()

from django.contrib.auth import get_user_model, authenticate
User = get_user_model()

print("=== FORCE CREATING FRESH SUPERUSER ===")

try:
    # Delete ALL existing users to start fresh
    User.objects.all().delete()
    print("✓ All users deleted")
except Exception as e:
    print(f"Warning: Could not delete users: {e}")

# قائمة كلمات المرور البديلة لتجنب مشاكل اتجاه الكتابة
passwords = [
    'Owner2026Iraq',    # الأصلية
    'Owner2026Irq',     # بديلة بدون q في النهاية
    'Owner@2026#Iraq',  # مع رموز
    'Iraq2026Owner',    # معكوسة
    'owner2026IRAQ',    # بحروف صغيرة وكبيرة
]

# إنشاء المستخدم
print("Creating fresh superuser...")
try:
    user = User.objects.create_user(
        username='owner',
        email='owner@clothingstore.iq',
        password=passwords[0]  # نجرب الأولى أولاً
    )
    
    # Force superuser status
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    
    if hasattr(user, 'role'):
        user.role = 'admin'
        
    user.save()

    print('✓ Fresh superuser created successfully!')
    print(f'Username: {user.username}')
    print(f'Primary Password: {passwords[0]}')
    
    # اختبار تسجيل الدخول بالكلمات المختلفة
    print(f"\n=== TESTING LOGIN WITH DIFFERENT PASSWORDS ===")
    working_passwords = []
    
    for pwd in passwords:
        test_user = authenticate(username='owner', password=pwd)
        if test_user is not None:
            print(f"✓ Password '{pwd}' works!")
            working_passwords.append(pwd)
        else:
            print(f"✗ Password '{pwd}' failed")
    
    # عرض كلمات المرور التي تعمل
    print(f"\n=== WORKING PASSWORDS ===")
    if working_passwords:
        for i, pwd in enumerate(working_passwords, 1):
            print(f"{i}. {pwd}")
        print(f"\nاستخدم إحدى هذه الكلمات للدخول!")
    else:
        print("⚠️ لا توجد كلمات مرور تعمل!")
        
    # عرض معلومات المستخدم
    print(f"\n=== USER INFO ===")
    print(f"Username: owner")
    print(f"Email: owner@clothingstore.iq")
    print(f"Is staff: {user.is_staff}")
    print(f"Is superuser: {user.is_superuser}")
    print(f"Is active: {user.is_active}")
        
except Exception as e:
    print(f"Error creating superuser: {e}")
    import traceback
    traceback.print_exc()

print("\n=== SUPERUSER CREATION COMPLETED ===")
