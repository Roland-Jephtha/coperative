from django.db import models

class Meeting(models.Model):
    cooperative = models.ForeignKey('cooperatives.Cooperative', on_delete=models.CASCADE, related_name='meetings')
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=255, null=True, blank=True)
    agenda = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} on {self.date}"
