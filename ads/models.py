from django.db import models
from django.db.models import Q
from django.utils import timezone
import os
from django.conf import settings

def _normalize_url(value):
    try:
        s = str(value).strip()
    except Exception:
        return ''
    if not s:
        return ''
    s = s.replace('https://https//', 'https://').replace('http://http//', 'http://')
    if s.startswith('https//'):
        s = 'https://' + s[len('https//'):]
    if s.startswith('http//'):
        s = 'http://' + s[len('http//'):]
    if s.startswith('//'):
        s = 'https:' + s
    try:
        from urllib.parse import urlparse
        p = urlparse(s)
        host = (p.netloc or '').lower()
        if host.endswith('r2.cloudflarestorage.com') or host.endswith('r2.dev'):
            base = (
                getattr(settings, 'R2_PUBLIC_BASE_URL', '')
                or os.environ.get('R2_PUBLIC_BASE_URL', '')
                or getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', '')
                or os.environ.get('R2_PUBLIC_DOMAIN', '')
            )
            if base:
                base = str(base).strip().replace('https://https//', 'https://').replace('http://http//', 'http://')
                if base.startswith('https//'):
                    base = 'https://' + base[len('https//'):]
                if base.startswith('http//'):
                    base = 'http://' + base[len('http//'):]
                if base.startswith('http://') or base.startswith('https://'):
                    return f"{base.rstrip('/')}{p.path}"
            if p.path:
                return p.path if p.path.startswith('/') else f"/{p.path}"
    except Exception:
        pass
    return s

class Banner(models.Model):
    PLACEMENTS = (
        ("home_top", "Home Top"),
        ("home_middle", "Home Middle"),
        ("home_bottom", "Home Bottom"),
    )
    LINK_TYPES = (
        ("none", "None"),
        ("product", "Product"),
        ("category", "Category"),
        ("store", "Store"),
        ("url", "URL"),
    )
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="ads/banners/")
    link_type = models.CharField(max_length=20, choices=LINK_TYPES, default="none")
    link_target = models.CharField(max_length=200, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_dismissible = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    placement = models.CharField(max_length=20, choices=PLACEMENTS, default="home_top")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-priority", "-updated_at")
        indexes = [
            models.Index(fields=["placement"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.title

    def get_image_url(self):
        try:
            if self.image:
                return _normalize_url(self.image.url)
        except Exception:
            pass
        return ''

class Advertisement(models.Model):
    POSITION_CHOICES = [
        ('home_top', 'الصفحة الرئيسية - أعلى'),
        ('home_middle', 'الصفحة الرئيسية - منتصف'),
        ('home_bottom', 'الصفحة الرئيسية - أسفل'),
        ('sidebar', 'الشريط الجانبي'),
        ('product_page', 'صفحة المنتج'),
        ('mobile_banner', 'التطبيق - بانر رئيسي'),
        ('mobile_card', 'التطبيق - كارد'),
        ('mobile_popup', 'التطبيق - نافذة منبثقة'),
    ]
    TYPE_CHOICES = [
        ('banner', 'بانر'),
        ('card', 'كارد'),
        ('popup', 'نافذة منبثقة'),
        ('slider', 'سلايدر'),
    ]
    title = models.CharField('العنوان', max_length=200)
    description = models.TextField('الوصف', blank=True)
    image = models.ImageField('الصورة', upload_to='ads/')
    link = models.URLField('الرابط', blank=True)
    position = models.CharField('الموضع', max_length=50, choices=POSITION_CHOICES)
    ad_type = models.CharField('النوع', max_length=20, choices=TYPE_CHOICES, default='banner')
    order = models.IntegerField('الترتيب', default=0)
    is_active = models.BooleanField('نشط', default=True)
    start_date = models.DateTimeField('تاريخ البدء', default=timezone.now)
    end_date = models.DateTimeField('تاريخ الانتهاء', null=True, blank=True)
    impressions = models.IntegerField('المشاهدات', default=0)
    clicks = models.IntegerField('النقرات', default=0)
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ التعديل', auto_now=True)

    class Meta:
        ordering = ['order', '-created_at'],
        indexes = [
            models.Index(fields=["position"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.title

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True

    @classmethod
    def get_active_ads(cls, position=None):
        now = timezone.now()
        queryset = cls.objects.filter(
            is_active=True,
            start_date__lte=now,
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        )
        if position:
            queryset = queryset.filter(position=position)
        return queryset.order_by('order', '-created_at')

    def get_image_url(self):
        try:
            if self.image:
                return _normalize_url(self.image.url)
        except Exception:
            pass
        return ''
