from django.db import migrations, models

def backfill_user_role_flags(apps, schema_editor):
    User = apps.get_model("core", "User")
    User.objects.filter(role="store_admin").update(is_store_admin=True, is_customer=True)
    User.objects.filter(role="customer").update(is_customer=True)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0056_alter_order_total_amount"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_customer",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="user",
            name="is_store_admin",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(backfill_user_role_flags, migrations.RunPython.noop),
    ]
