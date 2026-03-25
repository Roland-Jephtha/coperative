from apps.accounts.models import User, UserRole
from apps.cooperatives.models import Cooperative

try:
    user = User.objects.get(username='jephtha')
    coop = Cooperative.objects.first()
    if not coop:
        coop = Cooperative.objects.create(name='Demo Cooperative')
    user.cooperative = coop
    user.role = UserRole.COOP_ADMIN
    user.save()
    print('Link Successful')
except Exception as e:
    print(f'Error: {e}')
