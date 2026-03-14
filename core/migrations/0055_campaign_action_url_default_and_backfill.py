from django.db import migrations, models


def backfill_campaign_action_url(apps, schema_editor):
    Campaign = apps.get_model("core", "Campaign")
    Campaign.objects.filter(action_url="/stores/").update(action_url="/products/")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0054_product_is_on_offer_product_offer_badge_text_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="campaign",
            name="action_url",
            field=models.CharField(blank=True, default="/products/", max_length=255),
        ),
        migrations.RunPython(backfill_campaign_action_url, migrations.RunPython.noop),
    ]
