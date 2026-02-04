from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import ProductImage


@receiver(post_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    try:
        f = getattr(instance, 'image', None)
        if f and hasattr(f, 'storage') and f.name:
            try:
                f.delete(save=False)
            except Exception:
                pass
    except Exception:
        pass

