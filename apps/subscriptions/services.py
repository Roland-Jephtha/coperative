from decimal import Decimal
from apps.accounts.models import User, UserRole

def calculate_subscription_cost(cooperative):
    try:
        subscription = cooperative.subscription
        if not subscription or not subscription.plan:
            return Decimal('0.00')

        active_members_count = User.objects.filter(
            cooperative=cooperative, 
            role=UserRole.MEMBER, 
            is_active=True
        ).count()

        total_cost = Decimal(active_members_count) * subscription.plan.annual_price_per_member
        return total_cost
    except Exception:
        return Decimal('0.00')
