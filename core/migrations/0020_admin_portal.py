from django.db import migrations, models
import django.conf


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0019_address_is_default_address_plus_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="admin_role",
            field=models.CharField(blank=True, default="", max_length=20, choices=[
                ("SUPER_ADMIN", "مشرف عام"),
                ("OWNER", "مالك"),
                ("SUPPORT", "دعم"),
                ("DELIVERY", "توصيل"),
            ]),
        ),
        migrations.CreateModel(
            name="AdminAuditLog",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=100)),
                ("model", models.CharField(max_length=100)),
                ("object_id", models.CharField(max_length=100)),
                ("before", models.TextField(blank=True)),
                ("after", models.TextField(blank=True)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("ip", models.CharField(blank=True, max_length=45)),
                ("admin_user", models.ForeignKey(on_delete=models.deletion.CASCADE, to=django.conf.settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="AdminLoginAttempt",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username_or_email", models.CharField(max_length=150)),
                ("success", models.BooleanField(default=False)),
                ("reason", models.CharField(blank=True, max_length=200)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("ip", models.CharField(blank=True, max_length=45)),
            ],
        ),
    ]
