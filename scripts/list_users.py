from core.models import User

def run():
    qs = User.objects.all().order_by('-is_superuser', 'id')[:10]
    for u in qs:
        print(f"username={u.username} is_superuser={u.is_superuser} phone={u.phone}")
