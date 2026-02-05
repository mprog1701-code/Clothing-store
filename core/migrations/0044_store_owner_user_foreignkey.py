from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0043_add_indexes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='store',
            name='owner_user',
            field=models.ForeignKey(
                to='core.user',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
                related_name='owned_store',
            ),
        ),
    ]
