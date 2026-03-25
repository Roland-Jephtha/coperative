from django.db.models import Sum
from .models import Contribution
import datetime

def get_member_total_savings(member):
    result = Contribution.objects.filter(member=member).aggregate(total=Sum('amount'))
    return result['total'] or 0.00

def get_member_contributions_by_year(member, year):
    result = Contribution.objects.filter(member=member, contribution_date__year=year).aggregate(total=Sum('amount'))
    return result['total'] or 0.00

def get_cooperative_total_savings(cooperative):
    result = Contribution.objects.filter(cooperative=cooperative).aggregate(total=Sum('amount'))
    return result['total'] or 0.00
