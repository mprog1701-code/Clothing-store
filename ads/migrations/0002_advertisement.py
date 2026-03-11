from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ads", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Advertisement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("image", models.ImageField(upload_to="ads/")),
                ("link", models.CharField(blank=True, max_length=255)),
                ("position", models.CharField(choices=[("home_top", "Home Top"), ("home_middle", "Home Middle"), ("home_bottom", "Home Bottom")], default="home_top", max_length=20)),
                ("ad_type", models.CharField(choices=[("image", "Image"), ("banner", "Banner")], default="image", max_length=20)),
                ("order", models.IntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("order", "-updated_at"),
            },
        ),
        migrations.AddIndex(
            model_name="advertisement",
            index=models.Index(fields=["position"], name="ads_adverti_position_9f0b7c_idx"),
        ),
        migrations.AddIndex(
            model_name="advertisement",
            index=models.Index(fields=["is_active"], name="ads_adverti_is_activ_7b5b58_idx"),
        ),
    ]
