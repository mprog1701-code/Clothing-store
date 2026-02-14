from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0049_orderitem_negotiated_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('proposed_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('proposal_status', models.CharField(blank=True, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], max_length=20, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.user')),
                ('variant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.productvariant')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['user'], name='core_cartitem_user_idx'),
                    models.Index(fields=['product'], name='core_cartitem_product_idx'),
                    models.Index(fields=['variant'], name='core_cartitem_variant_idx'),
                ],
                'unique_together': {('user', 'product', 'variant')},
            },
        ),
    ]
