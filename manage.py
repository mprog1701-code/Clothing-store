#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import importlib.util

def main():
    """Run administrative tasks."""
    settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', '').strip()
    module_aliases = {
        'clothing_store_settings': 'clothing_store.settings_dev',
        'clothing_store_settings_dev': 'clothing_store.settings_dev',
        'clothing_store_settings_railway': 'clothing_store.settings_railway',
    }
    if settings_module in module_aliases:
        os.environ['DJANGO_SETTINGS_MODULE'] = module_aliases[settings_module]
        settings_module = os.environ['DJANGO_SETTINGS_MODULE']
    if not settings_module:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'clothing_store.settings_dev'
    else:
        if importlib.util.find_spec(settings_module) is None:
            fallback = 'clothing_store.settings_railway' if os.environ.get('RAILWAY_ENVIRONMENT') else 'clothing_store.settings_dev'
            os.environ['DJANGO_SETTINGS_MODULE'] = fallback

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
