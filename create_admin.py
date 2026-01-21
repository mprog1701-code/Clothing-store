from core.models import User

# Create superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com', 
        password='admin123',
        phone='07700000000',
        city='بغداد',
        role='admin'
    )
    print("✅ تم إنشاء حساب الأدمن بنجاح!")
    print("اسم المستخدم: admin")
    print("كلمة المرور: admin123")
else:
    print("⚠️ حساب الأدمن موجود بالفعل")
