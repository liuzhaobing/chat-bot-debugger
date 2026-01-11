import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from chat.models import Provider

print("--- Providers in DB ---")
providers = Provider.objects.all()
for p in providers:
    print(f"ID: {p.id}, Name: {p.name}, Active: {p.is_active}, URL: {p.base_url}")
print(f"Total: {len(providers)}")
