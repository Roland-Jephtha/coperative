import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coperative.settings')
django.setup()

from apps.accounts.models import User

try:
    user = User.objects.get(username='jephtha')
    print(f"User: {user.username}")
    print(f"Role: {user.role}")
    print(f"Cooperative: {user.cooperative}")
    if user.cooperative:
        print(f"Cooperative Name: {user.cooperative.name}")
except User.DoesNotExist:
    print("User 'jephtha' not found.")
except Exception as e:
    import traceback
    traceback.print_exc()
