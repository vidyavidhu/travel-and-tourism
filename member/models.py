from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dob = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=250,null=True, blank=True)
    phone = models.CharField(max_length=10,null=True, blank=True)
    gender = models.CharField(max_length=10,null=True, blank=True)
    image = models.ImageField(upload_to='uploads/members/',null=True, blank=True)
    bgroup = models.CharField(max_length=10,null=True, blank=True)
    emergency_contact = models.CharField(max_length=10,null=True, blank=True)
    emergency_name = models.CharField(max_length=100,null=True, blank=True)
    # emergency_relationship = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True) 
    is_coordinator = models.BooleanField(default=False)
    def __str__(self):
        return self.user.username

class Coordinator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True)
    is_authorised = models.BooleanField(default=False)
    authorised_pdf = models.FileField(upload_to='uploads/pdfs/',null=True, blank=True) 
    description = models.TextField(null=True, blank=True)  
    status = models.IntegerField(default=1) #0 for not active, 1 for active
    is_approved = models.BooleanField(default=False)
    def __str__(self):
        return self.user.username