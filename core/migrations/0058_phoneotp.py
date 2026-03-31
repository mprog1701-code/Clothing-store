from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0057_user_is_customer_user_is_store_admin'),
    ]

    operations = [
        migrations.CreateModel(
            name='PhoneOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(db_index=True, max_length=20)),
                ('purpose', models.CharField(choices=[('signup', 'signup'), ('reset', 'reset')], db_index=True, max_length=20)),
                ('code_hash', models.CharField(max_length=128)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('consumed_at', models.DateTimeField(blank=True, null=True)),
                ('attempts', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'indexes': [models.Index(fields=['phone', 'purpose'], name='core_phoneot_phone_04d6f4_idx'), models.Index(fields=['expires_at'], name='core_phoneot_expires_2f0ab3_idx')],
            },
        ),
    ]
