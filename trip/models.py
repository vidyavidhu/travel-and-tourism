from django.template.defaultfilters import default
from django.db import models
from member.models import Member,Coordinator
# Create your models here.

class TripCategory(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField(null=True, blank=True) 
    def __str__(self):
        return self.name


class DocumentType(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField(null=True, blank=True) 
    def __str__(self):
        return self.name

class Document(models.Model):
    member=models.ForeignKey(Member, on_delete=models.CASCADE)
    type=models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    file=models.FileField(upload_to='documents/',null=True, blank=True) 
    description=models.TextField(null=True, blank=True) 
    def __str__(self):
        return self.name



class VechicleType(models.Model):
    name=models.CharField(max_length=100)
    def __str__(self):
        return self.name



        

class Trip(models.Model):
    image = models.ImageField(upload_to='trips/',null=True, blank=True)    
    title = models.CharField(max_length=100) 
    category = models.ForeignKey(TripCategory, on_delete=models.CASCADE)
    location_from_name=models.CharField(max_length=250,default='')
    location_from_lattitude=models.CharField(max_length=250,default='0.000')
    location_from_longitude=models.CharField(max_length=250,default='0.000')
    location_to_name=models.CharField(max_length=250,default='')
    location_to_lattitude=models.CharField(max_length=250,default='0.00')
    location_to_longitude=models.CharField(max_length=250,default='0.000')
    distance=models.FloatField()
    from_date=models.DateField()
    from_time=models.TimeField()
    to_date=models.DateField()
    to_time=models.TimeField()
    duration=models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)  
    coordinator = models.ForeignKey(Coordinator, on_delete=models.CASCADE)
    guidelines = models.TextField(null=True, blank=True)
    status = models.IntegerField(default=1)  
    def __str__(self):
        return self.title

# class Vehicle(models.Model):
#     trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
#     type = models.ForeignKey(VechicleType, on_delete=models.CASCADE)
#     image = models.ImageField(upload_to='vehicle_images/',null=True, blank=True)    
#     seat_capacity = models.IntegerField()
#     vehicle_number = models.CharField(max_length=10)
#     contact_name=models.CharField(max_length=100)
#     contact_number=models.CharField(max_length=14) 
#     price_per_member = models.FloatField()
#     description = models.TextField(null=True, blank=True) 
#     status = models.IntegerField(default=1) #0 for not booked, 1 for booked
#     def __str__(self):
#         return self.vehicle_number

class Trip_Details(models.Model):
    trip=models.OneToOneField(Trip, on_delete=models.CASCADE) 
    max_members = models.IntegerField(default=1)
    no_of_members = models.IntegerField(default=1)
    estimated_cost=models.FloatField() 
    description=models.TextField(null=True, blank=True) 
    def __str__(self):
        return self.trip.title

class Trip_Members(models.Model):
    trip=models.ForeignKey(Trip, on_delete=models.CASCADE) 
    member=models.ForeignKey(Member, on_delete=models.CASCADE) 
    status = models.IntegerField(default=0) #0 for not Joined, 1 for  Joined, 2 for Cancelled
    payment_status = models.IntegerField(default=0) #0 for not paid, 1 for paid
    description = models.TextField(null=True, blank=True) 
    def __str__(self):
        return self.trip.title+" - "+self.member.name

class ActivityType(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField(null=True, blank=True) 
    def __str__(self):
        return self.name

class Trip_Day(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    date = models.DateField()
    def __str__(self):
        return f"{self.trip.title} - {self.date}"

class Itinerary(models.Model):
    trip_day = models.ForeignKey(Trip_Day, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    vehicle=models.ForeignKey(VechicleType,models.SET_NULL,null=True, blank=True)    
    date_start = models.DateField()
    time_start = models.TimeField()
    location_start_geo = models.CharField(max_length=250,default='0.000')
    location_start_name=models.CharField(max_length=250,default='')
    date_end = models.DateField()
    time_end = models.TimeField()
    distance = models.FloatField(default=0.00) #in kms
    travel_time = models.CharField(max_length=10,default='0.00') #in hrs
    location_end_geo = models.CharField(max_length=250,default='0.000')
    location_end_name=models.CharField(max_length=250,default='')
    spending_time = models.CharField(max_length=10,default='0.00') #in hrs
    location_image = models.ImageField(upload_to='location_images/',null=True, blank=True) 
    guidelines = models.TextField(null=True, blank=True) 
    description = models.TextField(null=True, blank=True) 
    def __str__(self):
        return self.title

from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta

@receiver(post_save, sender=Trip)
def auto_generate_trip_days(sender, instance, created, **kwargs):
    if instance.from_date and instance.to_date:
        current_date = instance.from_date
        while current_date <= instance.to_date:
            Trip_Day.objects.get_or_create(trip=instance, date=current_date)
            current_date += timedelta(days=1)

