from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0046_product_fit_type_productimage_video_file_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ErrorLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(choices=[('backend', 'backend'), ('frontend', 'frontend')], default='backend', max_length=10)),
                ('error_type', models.CharField(max_length=100)),
                ('message', models.TextField()),
                ('file_path', models.TextField(blank=True)),
                ('line_number', models.IntegerField(default=0)),
                ('url', models.CharField(blank=True, max_length=500)),
                ('fingerprint', models.CharField(max_length=64, unique=True)),
                ('occurrences', models.IntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_seen', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.user')),
            ],
        ),
        migrations.AddIndex(
            model_name='errorlog',
            index=models.Index(fields=['source'], name='core_error_source_idx'),
        ),
        migrations.AddIndex(
            model_name='errorlog',
            index=models.Index(fields=['file_path'], name='core_error_file_idx'),
        ),
        migrations.AddIndex(
            model_name='errorlog',
            index=models.Index(fields=['line_number'], name='core_error_line_idx'),
        ),
    ]

