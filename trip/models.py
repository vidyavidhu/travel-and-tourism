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
    @property
    def total_duration_days(self):
        if self.from_date and self.to_date:
            delta = self.to_date - self.from_date
            return delta.days + 1
        return 1

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
    time_start = models.TimeField()
    location_from_name=models.CharField(max_length=250,default='')
    location_from_lattitude=models.CharField(max_length=250,default='0.000')
    location_from_longitude=models.CharField(max_length=250,default='0.000')
    time_end = models.TimeField()
    distance = models.FloatField(default=0.00, blank=True, null=True) #in kms
    duration = models.CharField(max_length=10,default='0.00', blank=True, null=True) #in hrs
    location_to_name=models.CharField(max_length=250,default='', blank=True, null=True)
    location_to_lattitude=models.CharField(max_length=250,default='0.000', blank=True, null=True)
    location_to_longitude=models.CharField(max_length=250,default='0.000', blank=True, null=True)
    spending_time = models.CharField(max_length=10,default='0.00') #in hrs
    location_image = models.ImageField(upload_to='location_images/',null=True, blank=True) 
    guidelines = models.TextField(null=True, blank=True) 
    description = models.TextField(null=True, blank=True) 
    def save(self, *args, **kwargs):
        if not self.location_to_name:
            self.location_to_name = self.location_from_name
            self.location_to_lattitude = self.location_from_lattitude
            self.location_to_longitude = self.location_from_longitude
            self.distance = 0.0
            self.duration = '0'
        super().save(*args, **kwargs)
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

class Gallery(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE)  
    uploaded_by = models.ForeignKey(Trip_Members, on_delete=models.CASCADE, null=True, blank=True)  
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='gallery/images/',null=True, blank=True) 
    video = models.FileField(upload_to='gallery/videos/',null=True, blank=True)
    description = models.TextField(null=True, blank=True) 
    date_time=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title

class Comments(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE)  
    message_by=models.ForeignKey(Trip_Members, on_delete=models.CASCADE)  
    text=models.TextField(null=True, blank=True) 
    image=models.ImageField(upload_to='message_images/',null=True, blank=True) 
    audio=models.FileField(upload_to='message_audio/',null=True, blank=True) 
    video=models.FileField(upload_to='message_video/',null=True, blank=True) 
    gif=models.FileField(upload_to='message_gif/',null=True, blank=True) 
    date_time=models.DateTimeField(auto_now_add=True) 
    def __str__(self):
        return str(self.text)[:50]

class Reply(models.Model):
    comment = models.ForeignKey(Comments, on_delete=models.CASCADE, related_name='replies')  
    reply_by=models.ForeignKey(Trip_Members, on_delete=models.CASCADE)  
    text=models.TextField(null=True, blank=True) 
    image=models.ImageField(upload_to='reply_images/',null=True, blank=True) 
    audio=models.FileField(upload_to='reply_audio/',null=True, blank=True) 
    video=models.FileField(upload_to='reply_video/',null=True, blank=True) 
    gif=models.FileField(upload_to='reply_gif/',null=True, blank=True) 
    emoji=models.CharField(max_length=10,null=True, blank=True) 
    date_time=models.DateTimeField(auto_now_add=True)    
    def __str__(self):
        return str(self.text)[:50]

class Reaction(models.Model):
    comment=models.ForeignKey(Comments, on_delete=models.CASCADE,null=True, blank=True)  
    is_reply=models.IntegerField(default=0) #0 for not reply, 1 for reply
    reply=models.ForeignKey(Reply, on_delete=models.CASCADE,null=True, blank=True)  
    member=models.ForeignKey(Trip_Members, on_delete=models.CASCADE)  
    date_time=models.DateTimeField(auto_now_add=True) 
    is_like=models.IntegerField(default=0) #0 for not liked, 1 for liked,2 for loved,3 for angry,4 for sad
    def __str__(self):
        return f"Reaction by {self.member}"
        
class Rating(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE)  
    member=models.ForeignKey(Trip_Members, on_delete=models.CASCADE)  
    rating=models.IntegerField() 
    def __str__(self):
        return str(self.rating)

