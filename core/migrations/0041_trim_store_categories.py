from django.db import migrations

def forwards(apps, schema_editor):
    Store = apps.get_model('core', 'Store')
    removed = ['electronics', 'food', 'home', 'beauty', 'sports', 'books', 'toys']
    try:
        Store.objects.filter(category__in=removed).update(category='clothing')
    except Exception:
        # If table not present or field missing in older states, ignore
        pass

def backwards(apps, schema_editor):
    # No reversal: categories removed from scope
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0040_backfill_storeowners'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

