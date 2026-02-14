from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0048_rename_core_error_source_idx_core_errorl_source_d2bc84_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="negotiated_price",
            field=models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True),
        ),
    ]
