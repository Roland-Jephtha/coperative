from django.db import models

class MemberProfile(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='member_profile')
    member_id_str = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"Profile: {self.user.get_full_name()}"
