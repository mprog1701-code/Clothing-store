from django.db import migrations


def forwards(apps, schema_editor):
    ProductVariant = apps.get_model('core', 'ProductVariant')
    ProductColor = apps.get_model('core', 'ProductColor')

    for v in ProductVariant.objects.all():
        name = (v.color or '').strip()
        if not name:
            continue
        color_obj, _ = ProductColor.objects.get_or_create(product_id=v.product_id, name=name)
        v.color_obj_id = color_obj.id
        v.save(update_fields=['color_obj'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_productcolor_productvariant_uniq_product_color_size_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, noop_reverse),
    ]

