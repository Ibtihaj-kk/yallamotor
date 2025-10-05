#!/usr/bin/env python
"""
Simple script to test the Django setup.
Run this script to verify that Django is properly installed and configured.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yallamotor_project.settings')
    try:
        django.setup()
        print("Django setup successful!")
        print(f"Django version: {django.get_version()}")
        print("\nInstalled apps:")
        from django.conf import settings
        for app in settings.INSTALLED_APPS:
            print(f"- {app}")
        print("\nDatabase configuration:")
        print(f"Engine: {settings.DATABASES['default']['ENGINE']}")
        print("\nSetup complete! You can now run:")
        print("python manage.py migrate")
        print("python manage.py createsuperuser")
        print("python manage.py runserver")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())