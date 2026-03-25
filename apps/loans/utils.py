import calendar
from decimal import Decimal
import datetime

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return sourcedate.replace(year=year, month=month, day=day)

def generate_loan_schedule(loan):
    from .models import RepaymentSchedule
    
    # Clean previous schedules if they exist
    loan.schedules.all().delete()
    
    if not loan.amount or not loan.duration_months:
        return
        
    principal = Decimal(str(loan.amount))
    interest_rate = Decimal(str(loan.interest_rate)) / Decimal('100.0')
    months = int(loan.duration_months)
    start_date = loan.approval_date if loan.approval_date else loan.application_date
    if not start_date:
        start_date = datetime.date.today()

    if loan.interest_type == 'FLAT':
        yearly_rate = interest_rate
        total_interest = principal * yearly_rate * (Decimal(months) / Decimal('12.0'))
        monthly_interest = total_interest / Decimal(months)
        monthly_principal = principal / Decimal(months)
        monthly_payment = monthly_principal + monthly_interest
        
        balance = principal
        for i in range(1, months + 1):
            due_date = add_months(start_date, i)
            balance -= monthly_principal
            RepaymentSchedule.objects.create(
                loan=loan,
                month_number=i,
                due_date=due_date,
                payment_amount=round(monthly_payment, 2),
                interest_amount=round(monthly_interest, 2),
                principal_amount=round(monthly_principal, 2),
                balance=round(max(balance, Decimal('0.00')), 2)
            )

    elif loan.interest_type == 'REDUCING':
        monthly_rate = interest_rate / Decimal('12.0')
        if monthly_rate == 0:
            monthly_payment = principal / Decimal(months)
        else:
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
        
        balance = principal
        for i in range(1, months + 1):
            due_date = add_months(start_date, i)
            interest_amount = balance * monthly_rate
            principal_amount = monthly_payment - interest_amount
            balance -= principal_amount
            
            RepaymentSchedule.objects.create(
                loan=loan,
                month_number=i,
                due_date=due_date,
                payment_amount=round(monthly_payment, 2),
                interest_amount=round(interest_amount, 2),
                principal_amount=round(principal_amount, 2),
                balance=round(max(balance, Decimal('0.00')), 2)
            )

    elif loan.interest_type == 'MONTHLY':
        monthly_interest = principal * interest_rate
        monthly_principal = principal / Decimal(months)
        monthly_payment = monthly_principal + monthly_interest
        
        balance = principal
        for i in range(1, months + 1):
            due_date = add_months(start_date, i)
            balance -= monthly_principal
            RepaymentSchedule.objects.create(
                loan=loan,
                month_number=i,
                due_date=due_date,
                payment_amount=round(monthly_payment, 2),
                interest_amount=round(monthly_interest, 2),
                principal_amount=round(monthly_principal, 2),
                balance=round(max(balance, Decimal('0.00')), 2)
            )
