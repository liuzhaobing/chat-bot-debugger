import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from chat.models import App

apps_data = [
    {
        "name": "Adobe Photoshop",
        "description": "Edit, stylize, refine images",
        "category": "featured",
        "is_featured": True
    },
    {
        "name": "Apple Music",
        "description": "Build playlists and find music",
        "category": "lifestyle",
        "is_featured": False
    },
    {
        "name": "Canva",
        "description": "Search, create, edit designs",
        "category": "featured",
        "is_featured": True
    },
    {
        "name": "Airtable",
        "description": "Add structured data to ChatGPT",
        "category": "productivity",
        "is_featured": False
    },
    {
        "name": "Booking.com",
        "description": "Find hotels, homes and more",
        "category": "lifestyle",
        "is_featured": False
    },
    {
        "name": "Expedia",
        "description": "Plan and book trips",
        "category": "lifestyle",
        "is_featured": False
    }
]

for app_data in apps_data:
    App.objects.get_or_create(
        name=app_data['name'],
        defaults={
            "description": app_data['description'],
            "category": app_data['category'],
            "is_featured": app_data['is_featured']
        }
    )

print("Seed data for Apps created successfully.")
