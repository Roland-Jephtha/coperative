from django.db import models

class TransactionStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'

class Contribution(models.Model):
    member = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='contributions')
    cooperative = models.ForeignKey('cooperatives.Cooperative', on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    contribution_date = models.DateField()
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='recorded_contributions')
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.amount}"
