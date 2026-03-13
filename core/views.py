
from django.core.management import call_command
from django.http import HttpResponse

def run_migrations(request):
    """
    Emergency view to run migrations on production
    """
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponse("Unauthorized - Superuser required", status=403)
    try:
        call_command('migrate')
        return HttpResponse("Migrations applied successfully! Database is now up to date.")
    except Exception as e:
        return HttpResponse(f"Error applying migrations: {str(e)}", status=500)
