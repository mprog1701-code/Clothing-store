from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_address_latitude_address_longitude'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='accuracy_m',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='address',
            name='formatted_address',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='address',
            name='provider',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AddField(
            model_name='address',
            name='provider_place_id',
            field=models.CharField(max_length=100, blank=True),
        ),
    ]

