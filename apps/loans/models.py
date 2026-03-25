from django.db import models
from decimal import Decimal

class LoanStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    ACTIVE = 'ACTIVE', 'Active'
    COMPLETED = 'COMPLETED', 'Completed'
    DEFAULTED = 'DEFAULTED', 'Defaulted'

class Loan(models.Model):
    member = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='loans')
    cooperative = models.ForeignKey('cooperatives.Cooperative', on_delete=models.CASCADE, related_name='loans')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.TextField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    interest_type = models.CharField(max_length=20, choices=[('FLAT', 'Flat'), ('REDUCING', 'Reducing'), ('MONTHLY', 'Monthly')])
    duration_months = models.IntegerField()
    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.PENDING)
    application_date = models.DateField(auto_now_add=True)
    approval_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_amount_due(self):
        """Principal + calculated interest."""
        return self.schedules.aggregate(total=models.Sum('payment_amount'))['total'] or self.amount
    
    @property
    def total_amount_paid(self):
        """Sum of all APPROVED repayments."""
        from apps.repayments.models import TransactionStatus
        return self.repayments.filter(status=TransactionStatus.APPROVED).aggregate(
            total=models.Sum('amount_paid')
        )['total'] or Decimal('0.00')

    @property
    def total_pending_paid(self):
        """Sum of all PENDING repayments."""
        from apps.repayments.models import TransactionStatus
        return self.repayments.filter(status=TransactionStatus.PENDING).aggregate(
            total=models.Sum('amount_paid')
        )['total'] or Decimal('0.00')

    @property
    def balance_remaining(self):
        """Remaining balance on the loan."""
        return self.total_amount_due - self.total_amount_paid

    def update_schedule_status(self):
        """
        Dynamically marks schedule items as paid based on cumulative payment history.
        Handles overpayments by rolling them into subsequent months.
        """
        paid_amount = self.total_amount_paid
        schedules = self.schedules.all().order_by('month_number')
        
        for item in schedules:
            if paid_amount >= item.payment_amount:
                item.amount_paid = item.payment_amount
                item.is_paid = True
                paid_amount -= item.payment_amount
            elif paid_amount > 0:
                item.amount_paid = paid_amount
                item.is_paid = False
                paid_amount = Decimal('0.00')
            else:
                item.amount_paid = Decimal('0.00')
                item.is_paid = False
            item.save()
        
        # If all schedules are paid and loan was active, mark as COMPLETED
        if self.status == LoanStatus.ACTIVE and not schedules.filter(is_paid=False).exists():
            self.status = LoanStatus.COMPLETED
            self.save()

    def generate_repayment_schedule(self):
        """Generates repayment milestones based on loan terms."""
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
        
        # Clear existing schedules
        self.schedules.all().delete()
        
        principal = self.amount
        duration = self.duration_months
        rate = self.interest_rate / Decimal('100.0')
        
        # For simplicity, calculating total interest upfront (Flat Rate)
        # Standard Flat Rate formula: Total Interest = Principal * Rate * (Duration/12)
        total_interest = principal * rate * (Decimal(str(duration)) / Decimal('12.0'))
        total_due = principal + total_interest
        monthly_payment = (total_due / Decimal(str(duration))).quantize(Decimal('0.01'))
        
        monthly_principal = (principal / Decimal(str(duration))).quantize(Decimal('0.01'))
        monthly_interest = (total_interest / Decimal(str(duration))).quantize(Decimal('0.01'))
        
        start_date = self.approval_date or timezone.now().date()
        current_balance = total_due
        
        for i in range(1, duration + 1):
            due_date = start_date + relativedelta(months=i)
            
            # Adjust last payment for rounding errors
            if i == duration:
                payment = current_balance
            else:
                payment = monthly_payment
                
            current_balance -= payment
            
            RepaymentSchedule.objects.create(
                loan=self,
                month_number=i,
                due_date=due_date,
                payment_amount=payment,
                principal_amount=monthly_principal if i < duration else principal - (monthly_principal * (duration - 1)),
                interest_amount=monthly_interest if i < duration else total_interest - (monthly_interest * (duration - 1)),
                balance=max(current_balance, Decimal('0.00')),
                amount_paid=Decimal('0.00'),
                is_paid=False
            )

    def __str__(self):
        return f"Loan {self.id} - {self.member.get_full_name()}"

class RepaymentSchedule(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='schedules')
    month_number = models.IntegerField()
    due_date = models.DateField()
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2)
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_paid = models.BooleanField(default=False)

    class Meta:
        ordering = ['month_number']

    def __str__(self):
        return f"Schedule {self.month_number} for Loan {self.loan_id}"
