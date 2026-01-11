from django.db import migrations

ALLOWED = {'women','men','kids','perfumes','cosmetics','watches','shoes','clothing'}

def forwards(apps, schema_editor):
    Store = apps.get_model('core', 'Store')
    for s in Store.objects.all():
        try:
            if s.category not in ALLOWED:
                s.category = 'clothing'
                s.save(update_fields=['category'])
        except Exception:
            pass

def backwards(apps, schema_editor):
    # No-op: cannot restore previous non-clothing categories reliably
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0022_store_currency_store_delivery_time_unit_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
