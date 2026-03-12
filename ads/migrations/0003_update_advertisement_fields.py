from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("ads", "0002_advertisement"),
    ]

    operations = [
        migrations.RenameField(
            model_name="advertisement",
            old_name="starts_at",
            new_name="start_date",
        ),
        migrations.RenameField(
            model_name="advertisement",
            old_name="ends_at",
            new_name="end_date",
        ),
        migrations.AddField(
            model_name="advertisement",
            name="impressions",
            field=models.IntegerField(default=0, verbose_name="المشاهدات"),
        ),
        migrations.AddField(
            model_name="advertisement",
            name="clicks",
            field=models.IntegerField(default=0, verbose_name="النقرات"),
        ),
        migrations.AlterField(
            model_name="advertisement",
            name="position",
            field=models.CharField(choices=[("home_top", "الصفحة الرئيسية - أعلى"), ("home_middle", "الصفحة الرئيسية - منتصف"), ("home_bottom", "الصفحة الرئيسية - أسفل"), ("sidebar", "الشريط الجانبي"), ("product_page", "صفحة المنتج"), ("mobile_banner", "التطبيق - بانر رئيسي"), ("mobile_card", "التطبيق - كارد"), ("mobile_popup", "التطبيق - نافذة منبثقة")], max_length=50, verbose_name="الموضع"),
        ),
        migrations.AlterField(
            model_name="advertisement",
            name="ad_type",
            field=models.CharField(choices=[("banner", "بانر"), ("card", "كارد"), ("popup", "نافذة منبثقة"), ("slider", "سلايدر")], default="banner", max_length=20, verbose_name="النوع"),
        ),
        migrations.AlterField(
            model_name="advertisement",
            name="link",
            field=models.URLField(blank=True, verbose_name="الرابط"),
        ),
        migrations.AlterField(
            model_name="advertisement",
            name="start_date",
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name="تاريخ البدء"),
        ),
        migrations.AlterField(
            model_name="advertisement",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء"),
        ),
        migrations.AlterField(
            model_name="advertisement",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="تاريخ التعديل"),
        ),
    ]
