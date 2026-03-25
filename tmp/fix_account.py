import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coperative.settings')
django.setup()

from apps.accounts.models import User, UserRole
from apps.cooperatives.models import Cooperative

try:
    user = User.objects.get(username='jephtha')
    coop = Cooperative.objects.first()
    
    if not coop:
        coop = Cooperative.objects.create(name="Demo Cooperative")
        print("Created a Demo Cooperative.")
    
    user.cooperative = coop
    user.role = UserRole.COOP_ADMIN
    user.save()
    
    print(f"Successfully linked user 'jephtha' to cooperative '{coop.name}'.")
    print(f"User role set to: {user.role}")
except User.DoesNotExist:
    print("User 'jephtha' not found. Please register or check username.")
except Exception as e:
    import traceback
    traceback.print_exc()
