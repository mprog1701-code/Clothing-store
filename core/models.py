from django.db import models
import os
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class SiteSettings(models.Model):
    """Site-wide settings that can be customized by the super owner"""
    site_name = models.CharField(max_length=100, default='متجر الملابس')
    site_description = models.TextField(max_length=500, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_address = models.TextField(blank=True)
    
    # Homepage customization
    homepage_title = models.CharField(max_length=200, default='متجر الملابس - أحدث صيحات الموضة')
    featured_stores_count = models.PositiveIntegerField(default=6)
    featured_products_count = models.PositiveIntegerField(default=8)
    
    # Delivery settings
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=15.00)
    free_delivery_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    
    # Social media
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    
    # Footer settings
    footer_tagline = models.CharField(max_length=200, default='تسوق بثقة وأمان من أفضل المتاجر')
    footer_description = models.TextField(max_length=500, default='نوفر لك أفضل المنتجات بأعلى جودة وأفضل الأسعار')
    footer_store_name = models.CharField(max_length=100, default='متجر الملابس')
    footer_copyright = models.CharField(max_length=200, default='جميع الحقوق محفوظة')
    
    # Footer quick links
    footer_link_1 = models.CharField(max_length=50, default='المتاجر')
    footer_link_1_url = models.CharField(max_length=100, default='/stores/')
    footer_link_2 = models.CharField(max_length=50, default='الأكثر مبيعاً')
    footer_link_2_url = models.CharField(max_length=100, default='/products/most-sold/')
    footer_link_3 = models.CharField(max_length=50, default='العروض الخاصة')
    footer_link_3_url = models.CharField(max_length=100, default='/featured-products/')
    
    # Appearance
    primary_color = models.CharField(max_length=7, default='#667eea')
    secondary_color = models.CharField(max_length=7, default='#764ba2')
    visitor_count = models.PositiveIntegerField(default=0)
    # Legal pages
    privacy_enabled = models.BooleanField(default=True)
    terms_enabled = models.BooleanField(default=True)
    contact_enabled = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'إعدادات الموقع'
        verbose_name_plural = 'إعدادات الموقع'
    
    def __str__(self):
        return 'إعدادات الموقع'


class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'عميل'),
        ('admin', 'صاحب متجر'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, unique=True)
    city = models.CharField(max_length=100)
    owner_key = models.CharField(max_length=50, blank=True, help_text='مفتاح خاص للمالك فقط')
    ADMIN_ROLE_CHOICES = [
        ('SUPER_ADMIN', 'مشرف عام'),
        ('OWNER', 'مالك'),
        ('SUPPORT', 'دعم'),
        ('DELIVERY', 'توصيل'),
    ]
    admin_role = models.CharField(max_length=20, choices=ADMIN_ROLE_CHOICES, blank=True, default='')
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Store(models.Model):
    # Removed store_owner limitation - now only admin manages stores
    CATEGORY_CHOICES = [
        ('women', 'ملابس نسائية'),
        ('men', 'ملابس رجالية'),
        ('kids', 'ملابس أطفال'),
        ('perfumes', 'عطور'),
        ('cosmetics', 'كوزمتك'),
        ('watches', 'ساعات'),
        ('shoes', 'أحذية'),
        ('clothing', 'ملابس عامة'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'})
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    address = models.TextField()
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='stores/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='clothing')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    delivery_time = models.CharField(max_length=50, default='30-45 دقيقة')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    status = models.CharField(max_length=10, choices=[('DRAFT','مسودة'),('ACTIVE','نشط'),('DISABLED','غير نشط')], default='ACTIVE')
    primary_color = models.CharField(max_length=7, blank=True, default='')
    secondary_color = models.CharField(max_length=7, blank=True, default='')
    free_delivery_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='IQD')
    delivery_time_value = models.PositiveIntegerField(default=0)
    delivery_time_unit = models.CharField(max_length=10, choices=[('hour','ساعة'),('day','يوم')], blank=True, default='')
    
    def __str__(self):
        return self.name

    @property
    def main_logo_url(self):
        try:
            if self.logo:
                return self.logo.url
        except Exception:
            pass
        from .models import Product
        p = Product.objects.filter(store=self).prefetch_related('images').first()
        if p:
            img = p.main_image or p.images.first()
            if img:
                u = img.get_image_url()
                if u:
                    return u
        return os.environ.get('DEFAULT_PLACEHOLDER_IMAGE_URL', 'https://placehold.co/120x120?text=Store')


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('men', 'رجالي'),
        ('women', 'نسائي'),
        ('kids', 'أطفال'),
        ('cosmetics', 'كوزمتك'),
        ('perfumes', 'عطور'),
        ('sports', 'رياضية'),
        ('casual', 'كاجوال'),
        ('formal', 'رسمية'),
        ('accessories', 'إكسسوارات'),
        ('watches', 'ساعات'),
        ('shoes', 'أحذية'),
    ]
    
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    SIZE_TYPE_CHOICES = [
        ('symbolic', 'رمزية'),
        ('numeric', 'رقمية'),
        ('none', 'بدون'),
    ]
    size_type = models.CharField(max_length=10, choices=SIZE_TYPE_CHOICES, default='symbolic')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.store.name}"
    
    @property
    def main_image(self):
        return self.images.filter(is_main=True).first()


class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='colors')
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=7, blank=True)

    class Meta:
        unique_together = ('product', 'name')

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    color = models.ForeignKey('ProductColor', on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    variant = models.ForeignKey('ProductVariant', on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    is_main = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    def get_image_url(self):
        try:
            if self.image_url:
                return self.image_url
            if self.image:
                try:
                    return self.image.url
                except Exception:
                    pass
            placeholder = os.environ.get('DEFAULT_PLACEHOLDER_IMAGE_URL')
            if placeholder:
                return placeholder
            return 'https://placehold.co/300x300?text=Image'
        except Exception:
            return 'https://placehold.co/300x300?text=Image'

    def clean(self):
        # Ensure consistency with product
        if self.color and self.color.product_id != self.product_id:
            raise ValidationError({'color': 'اللون لا ينتمي إلى نفس المنتج'})
        if self.variant and self.variant.product_id != self.product_id:
            raise ValidationError({'variant': 'النسخة لا تنتمي إلى نفس المنتج'})


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color_obj = models.ForeignKey('ProductColor', on_delete=models.CASCADE, related_name='variants', null=True, blank=True)
    size = models.CharField(max_length=20)
    stock_qty = models.IntegerField(validators=[MinValueValidator(0)])
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'color_obj', 'size'], name='uniq_product_color_size')
        ]

    def clean(self):
        if self.color_obj and self.product and self.color_obj.product_id != self.product_id:
            raise ValidationError('اللون لا ينتمي إلى نفس المنتج')
        if self.product_id:
            st = self.product.size_type
            if st == 'symbolic':
                allowed = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '3XL', '4XL']
                if self.size not in allowed:
                    raise ValidationError({'size': 'المقاس غير صالح لهذا المنتج'})
            elif st == 'numeric':
                allowed = [str(n) for n in range(28, 61, 2)]
                if self.size not in allowed:
                    raise ValidationError({'size': 'المقاس غير صالح لهذا المنتج'})
            elif st == 'none':
                self.size = 'ONE'

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color}"

    @property
    def price(self):
        return self.price_override or self.product.base_price

    @property
    def color(self):
        return self.color_obj.name if self.color_obj else ''


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    street = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    accuracy_m = models.IntegerField(blank=True, null=True)
    formatted_address = models.TextField(blank=True)
    provider = models.CharField(max_length=50, blank=True)
    provider_place_id = models.CharField(max_length=100, blank=True)
    plus_code = models.CharField(max_length=20, blank=True, default='')
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.city} - {self.area} - {self.street}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('accepted', 'تم القبول'),
        ('preparing', 'قيد التجهيز'),
        ('on_the_way', 'في الطريق'),
        ('delivered', 'تم التسليم'),
        ('canceled', 'ملغي'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'الدفع عند الاستلام'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod')
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"طلب #{self.id} - {self.user.username}"
    
    def calculate_total(self):
        items_total = sum(item.price * item.quantity for item in self.items.all())
        self.total_amount = items_total + self.delivery_fee
        return self.total_amount


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity} في طلب #{self.order.id}"
    
    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.variant.price if self.variant else self.product.base_price
        super().save(*args, **kwargs)


class Campaign(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    banner_image = models.ImageField(upload_to='campaigns/', blank=True, null=True)
    discount_percent = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    action_url = models.CharField(max_length=255, blank=True, default='/stores/')

    class Meta:
        verbose_name = 'حملة'
        verbose_name_plural = 'حملات'

    def __str__(self):
        return self.title

    @property
    def is_running(self):
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date


class AdminAuditLog(models.Model):
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    before = models.TextField(blank=True)
    after = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=45, blank=True)

    def __str__(self):
        return f"{self.admin_user.username} - {self.action} - {self.model}:{self.object_id}"


class AdminLoginAttempt(models.Model):
    username_or_email = models.CharField(max_length=150)
    success = models.BooleanField(default=False)
    reason = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=45, blank=True)

    def __str__(self):
        return f"{self.username_or_email} - {'success' if self.success else 'fail'}"
