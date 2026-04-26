import random
import string
from django.db import models
from django.utils import timezone
from datetime import timedelta


class Resident(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=False, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class VisitorAccessRequest(models.Model):
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    visitor_name = models.CharField(max_length=100)
    visitor_phone = models.CharField(max_length=20)
    access_code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.access_code:
            self.access_code = self._generate_unique_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def _generate_unique_code(self, length=8):
        chars = string.ascii_uppercase + string.digits
        while True:
            code = "".join(random.choices(chars, k=length))
            if not VisitorAccessRequest.objects.filter(access_code=code).exists():
                return code

    def is_valid(self):
        return self.used_at is None and timezone.now() < self.expires_at

    def use(self):
        if self.is_valid():
            self.used_at = timezone.now()
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.access_code} - {self.visitor_name}"


class BlacklistedAddress(models.Model):
    address = models.TextField(unique=True)
    reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address[:50]
