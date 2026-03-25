from django.db import models

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    annual_price_per_member = models.DecimalField(max_digits=10, decimal_places=2)
    max_members = models.IntegerField(null=True, blank=True, help_text="Null for unlimited")

    def __str__(self):
        return self.name

class CooperativeSubscription(models.Model):
    cooperative = models.OneToOneField('cooperatives.Cooperative', on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.cooperative.name} - {self.plan.name if self.plan else 'No Plan'}"
