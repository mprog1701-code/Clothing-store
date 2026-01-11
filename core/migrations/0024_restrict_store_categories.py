from django.db import migrations

ALLOWED = {'women','men','kids','clothing'}

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
    # No-op: removed categories cannot be restored reliably
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0023_clean_store_categories'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

