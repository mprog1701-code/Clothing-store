from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0042_product_status_alter_orderitem_product_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['status'], name='product_status_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['store'], name='product_store_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['created_at'], name='order_created_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['store'], name='order_store_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['user'], name='order_user_idx'),
        ),
        migrations.AddIndex(
            model_name='productvariant',
            index=models.Index(fields=['product'], name='variant_product_idx'),
        ),
        migrations.AddIndex(
            model_name='productimage',
            index=models.Index(fields=['product'], name='image_product_idx'),
        ),
    ]

