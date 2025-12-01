# Clothing Store Marketplace - Django Project

نظام ويب لإدارة وطلب الملابس يحتوي على ثلاثة أدوار رئيسية: عميل، صاحب متجر، وأدمن.

## المميزات

### العملاء (Customers)
- تسجيل الدخول/التسجيل
- تصفح المتاجر والمنتجات
- إضافة منتجات إلى السلة
- إتمام الطلبات مع اختيار عنوان التوصيل
- مشاهدة قائمة الطلبات السابقة

### أصحاب المتاجر (Store Owners)
- إدارة المتجر الخاص بهم
- إضافة/تعديل/حذف المنتجات
- إدارة المخزون (المقاسات والألوان)
- استعراض الطلبات الواردة وتغيير حالتها

### الأدمن (Admin)
- لوحة تحكم شاملة
- إدارة المتاجر (تفعيل/تعطيل)
- نظرة عامة على الإحصائيات
- إدارة المستخدمين

## التقنيات المستخدمة

- **Backend**: Django 4.2.7
- **API**: Django REST Framework
- **Database**: PostgreSQL (SQLite للتطوير)
- **Frontend**: Django Templates + Bootstrap 5
- **Authentication**: JWT

## التثبيت والتشغيل

### المتطلبات
- Python 3.8+
- PostgreSQL (اختياري، يمكن استخدام SQLite للتطوير)

### خطوات التثبيت

1. **استنساخ المشروع**:
```bash
git clone <repository-url>
cd clothing_store
```

2. **إنشاء بيئة افتراضية**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **تثبيت المتطلبات**:
```bash
pip install -r requirements.txt
```

4. **إعداد قاعدة البيانات**:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **إنشاء حساب سوبر أدمن**:
```bash
python manage.py createsuperuser
```

6. **تشغيل الخادم**:
```bash
python manage.py runserver
```

7. **الوصول إلى التطبيق**:
- الموقع: http://127.0.0.1:8000/
- لوحة الأدمن: http://127.0.0.1:8000/admin/

## API Endpoints

### المصادقة
- `POST /api/auth/register/` - تسجيل مستخدم جديد
- `POST /api/auth/login/` - تسجيل الدخول
- `GET /api/auth/me/` - بيانات المستخدم الحالي

### المتاجر
- `GET /api/stores/` - قائمة المتاجر
- `GET /api/stores/{id}/` - تفاصيل متجر محدد
- `GET/POST/PUT/PATCH /api/stores/my_store/` - إدارة المتجر الخاص (لصاحب المتجر)

### المنتجات
- `GET /api/products/` - قائمة المنتجات
- `GET /api/products/{id}/` - تفاصيل منتج محدد
- `GET/POST/PUT/PATCH/DELETE /api/products/my_products/` - إدارة منتجات المتجر (لصاحب المتجر)

### العناوين
- `GET /api/addresses/` - عناوين المستخدم
- `POST /api/addresses/` - إضافة عنوان جديد
- `PUT/PATCH /api/addresses/{id}/` - تعديل عنوان
- `DELETE /api/addresses/{id}/` - حذف عنوان

### الطلبات
- `GET /api/orders/` - طلبات المستخدم
- `POST /api/orders/` - إنشاء طلب جديد
- `GET /api/orders/{id}/` - تفاصيل طلب محدد
- `PATCH /api/orders/{id}/update_status/` - تغيير حالة الطلب (لصاحب المتجر)
- `GET /api/orders/store_orders/` - طلبات المتجر (لصاحب المتجر)
- `GET /api/orders/all_orders/` - جميع الطلبات (للأدمن)

## هيكل قاعدة البيانات

### المستخدمين (User)
- username, email, password
- role: customer/store_owner/admin
- phone, city

### المتاجر (Store)
- name, owner, city, address
- description, is_active

### المنتجات (Product)
- name, store, description, base_price
- category, is_active

### متغيرات المنتج (ProductVariant)
- product, size, color, stock_qty
- price_override

### الطلبات (Order)
- user, store, status, total_amount
- delivery_fee, payment_method, address

### عناصر الطلب (OrderItem)
- order, product, variant, quantity, price

## ملاحظات مهمة

1. **الصلاحيات**: تم تطبيق نظام صلاحيات صارم لضمان أن كل مستخدم يمكنه الوصول فقط إلى البيانات الخاصة به
2. **المخزون**: يتم تحديث المخزون تلقائياً عند إنشاء الطلبات
3. **الدفع**: في هذه المرحلة يتم الدفع عند الاستلام فقط (COD)
4. **التوصيل**: رسوم التوصيل ثابتة (50 ريال)

## التطوير المستقبلي

- إضافة نظام دفع إلكتروني
- نظام تقييمات ومراجعات
- نظام إشعارات
- تطبيق جوال
- نظام خصومات وكوبونات

## الدعم

لأي استفسارات أو مشاكل، يرجى فتح issue في المستودع.