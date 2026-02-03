from django.db import migrations

def forwards(apps, schema_editor):
    Store = apps.get_model('core', 'Store')
    removed = ['electronics', 'food', 'home', 'beauty', 'sports', 'books', 'toys']
    try:
        Store.objects.filter(category__in=removed).update(category='clothing')
    except Exception:
        pass

def backwards(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0011_store_logo_alter_product_category_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
