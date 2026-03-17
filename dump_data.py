import os
import django
import sys
import json
from django.core import serializers

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType

def dump_it():
    print("📦 Exporting local data (UTF-8)...")
    # Exclude contenttypes and permissions to avoid conflicts on server
    excluded_apps = ['contenttypes', 'auth.Permission']
    
    # Get all models except excluded ones
    objects = []
    for model in django.apps.apps.get_models():
        if model._meta.app_label not in excluded_apps:
            objects.extend(model.objects.all())
            
    # Serialize to JSON with natural keys
    data = serializers.serialize(
        'json', 
        objects, 
        indent=4, 
        use_natural_foreign_keys=True, 
        use_natural_primary_keys=True
    )
    
    # Write to file with UTF-8 encoding
    with open('data.json', 'w', encoding='utf-8') as f:
        f.write(data)
    
    print("✅ Successfully saved to data.json")

if __name__ == "__main__":
    dump_it()
