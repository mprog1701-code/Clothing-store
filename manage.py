#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    
    # Check if we should use production settings
    if os.path.exists(os.path.join(os.path.dirname(__file__), 'clothing_store', 'settings_production.py')):
        # Only use production settings if explicitly requested or if we are on Railway
        if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('DJANGO_SETTINGS_MODULE') == 'clothing_store.settings_production':
             os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings_production')
        else:
             os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings')

    # Ensure DATABASE_URL is handled correctly for migrations
    if 'DATABASE_URL' in os.environ:
        import dj_database_url
        
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
