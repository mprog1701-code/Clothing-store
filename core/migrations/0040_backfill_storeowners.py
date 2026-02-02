from django.db import migrations

def backfill_storeowners(apps, schema_editor):
    User = apps.get_model('core', 'User')
    Store = apps.get_model('core', 'Store')
    StoreOwner = apps.get_model('core', 'StoreOwner')

    def get_or_create_owner_for_user(u):
        phone = (u.phone or '').strip()
        owner = None
        if phone:
            owner = StoreOwner.objects.filter(phone=phone).order_by('id').first()
        if owner is None:
            full_name = (u.get_full_name() or u.username or '').strip()
            owner = StoreOwner.objects.create(full_name=full_name or 'مالك', phone=phone)
        return owner

    # Backfill owners for users with admin/store_admin roles or username starting with owner_
    qs_users = User.objects.all()
    qs_users = qs_users.filter(role__in=['admin', 'store_admin']) | qs_users.filter(username__startswith='owner_')
    for u in qs_users:
        try:
            owner = get_or_create_owner_for_user(u)
            # Link stores owned by this user
            for s in Store.objects.filter(owner_id=u.id):
                if s.owner_profile_id is None:
                    s.owner_profile_id = owner.id
                if s.owner_user_id is None:
                    s.owner_user_id = u.id
                s.save(update_fields=['owner_profile_id', 'owner_user_id'])
        except Exception:
            continue

    # Link stores with owner_phone but without owner_profile
    stores_with_phone = Store.objects.exclude(owner_phone='').filter(owner_profile_id__isnull=True)
    for s in stores_with_phone:
        try:
            phone = (s.owner_phone or '').strip()
            owner = None
            if phone:
                owner = StoreOwner.objects.filter(phone=phone).order_by('id').first()
            if owner is None:
                full_name = (s.owner_contact_name or '').strip() or 'مالك'
                owner = StoreOwner.objects.create(full_name=full_name, phone=phone)
            s.owner_profile_id = owner.id
            s.save(update_fields=['owner_profile_id'])
        except Exception:
            continue

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0039_store_owner_user_alter_store_owner_alter_user_role_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_storeowners, migrations.RunPython.noop),
    ]

