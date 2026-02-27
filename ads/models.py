from django.db import models

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
