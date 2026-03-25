from django.db import models

class TransactionStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'

class LoanRepayment(models.Model):
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, related_name='repayments')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    balance_remaining = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Repayment {self.amount_paid} for Loan {self.loan_id}"
