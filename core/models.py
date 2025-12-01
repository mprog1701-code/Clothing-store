from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


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
    
    class Meta:
        verbose_name = 'إعدادات الموقع'
        verbose_name_plural = 'إعدادات الموقع'
    
    def __str__(self):
        return 'إعدادات الموقع'


class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'عميل'),
        ('admin', 'مدير'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, unique=True)
    city = models.CharField(max_length=100)
    owner_key = models.CharField(max_length=50, blank=True, help_text='مفتاح خاص للمالك فقط')
    
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
        ('clothing', 'ملابس عامة'),
        ('electronics', 'إلكترونيات'),
        ('food', 'مطاعم'),
        ('home', 'منزل'),
        ('beauty', 'جمال'),
        ('sports', 'رياضة'),
        ('books', 'كتب'),
        ('toys', 'ألعاب'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'})
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    address = models.TextField()
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='clothing')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    delivery_time = models.CharField(max_length=50, default='30-45 دقيقة')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    
    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('men', 'رجالي'),
        ('women', 'نسائي'),
        ('kids', 'أطفال'),
        ('sports', 'رياضية'),
        ('casual', 'كاجوال'),
        ('formal', 'رسمية'),
        ('accessories', 'إكسسوارات'),
        ('electronics', 'إلكترونيات'),
        ('beauty', 'جمال'),
        ('watches', 'ساعات'),
    ]
    
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.store.name}"
    
    @property
    def main_image(self):
        return self.images.filter(is_main=True).first()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    is_main = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    def get_image_url(self):
        """Get the image URL, preferring image_url over image field"""
        if self.image_url:
            return self.image_url
        elif self.image:
            return self.image.url
        return None


class ProductVariant(models.Model):
    SIZE_CHOICES = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
        ('3XL', '3XL'),
        ('4XL', '4XL'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    color = models.CharField(max_length=50)
    stock_qty = models.IntegerField(validators=[MinValueValidator(0)])
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color}"
    
    @property
    def price(self):
        return self.price_override or self.product.base_price


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    street = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    
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