from django.db import migrations


def enable_flags(apps, schema_editor):
    FeatureFlag = apps.get_model('core', 'FeatureFlag')
    keys = ['NEW_ARRIVALS_SECTION', 'OWNER_DASHBOARD_REPORTS']
    for key in keys:
        obj, _ = FeatureFlag.objects.get_or_create(
            key=key,
            defaults={'enabled': True, 'scope': 'global'}
        )
        obj.enabled = True
        obj.scope = 'global'
        obj.store_id = None
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_featureflag'),
    ]

    operations = [
        migrations.RunPython(enable_flags, migrations.RunPython.noop),
    ]

