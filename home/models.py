from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dob = models.DateField()
    address = models.CharField(max_length=250)
    phone = models.CharField(max_length=10)
    gender = models.CharField(max_length=10)
    image = models.ImageField(upload_to='members/',null=True, blank=True)
    bgroup = models.CharField(max_length=10)
    emergency_contact = models.CharField(max_length=10)
    emergency_name = models.CharField(max_length=100)
    # emergency_relationship = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True) 
    def __str__(self):
        return self.name

class Coordinator(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE)
    is_authorised = models.BooleanField(default=False)
    authorised_pdf = models.FileField(upload_to='authorised_pdfs/',null=True, blank=True) 
    description = models.TextField(null=True, blank=True)  
    status = models.IntegerField(default=1) #0 for not active, 1 for active
    def __str__(self):
        return self.member.name

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
    location=models.CharField(max_length=250)
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

class Vehicle(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    type = models.ForeignKey(VechicleType, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='vehicle_images/',null=True, blank=True)    
    seat_capacity = models.IntegerField()
    vehicle_number = models.CharField(max_length=10)
    contact_name=models.CharField(max_length=100)
    contact_number=models.CharField(max_length=14) 
    price_per_member = models.FloatField()
    description = models.TextField(null=True, blank=True) 
    status = models.IntegerField(default=1) #0 for not booked, 1 for booked
    def __str__(self):
        return self.vehicle_type.name+" - "+self.vehicle_number+" - "+self.contact_name

class Trip_Details(models.Model):
    trip=models.OneToOneField(Trip, on_delete=models.CASCADE) 
    max_members = models.IntegerField(default=1)
    no_of_members = models.IntegerField(default=0)
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
    activity_type=models.ForeignKey(ActivityType, on_delete=models.CASCADE)
    vehicle=models.ForeignKey(Vehicle, on_delete=models.CASCADE)    
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=250)
    location_image = models.ImageField(upload_to='location_images/',null=True, blank=True) 
    guidelines = models.TextField(null=True, blank=True) 
    description = models.TextField(null=True, blank=True) 
    def __str__(self):
        return self.name

class Itinerary(models.Model):
    trip_day = models.ForeignKey(Trip_Day, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    vehicle=models.ForeignKey(Vehicle, on_delete=models.CASCADE)    
    date_start = models.DateField()
    time_start = models.TimeField()
    location_start_geo = models.CharField(max_length=250)
    location_start_name=models.CharField(max_length=250)
    date_end = models.DateField()
    time_end = models.TimeField()
    distance = models.FloatField() #in kms
    travel_time = models.CharField(max_length=10) #in hrs
    location_end_geo = models.CharField(max_length=250)
    location_end_name=models.CharField(max_length=250)
    spending_time = models.CharField(max_length=10) #in hrs
    location_image = models.ImageField(upload_to='location_images/',null=True, blank=True) 
    guidelines = models.TextField(null=True, blank=True) 
    description = models.TextField(null=True, blank=True) 
    def __str__(self):
        return self.name

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
        return self.comment

class Reply(models.Model):
    comment = models.ForeignKey(Comments, on_delete=models.CASCADE)  
    reply_by=models.ForeignKey(Trip_Members, on_delete=models.CASCADE)  
    text=models.TextField(null=True, blank=True) 
    image=models.ImageField(upload_to='reply_images/',null=True, blank=True) 
    audio=models.FileField(upload_to='reply_audio/',null=True, blank=True) 
    video=models.FileField(upload_to='reply_video/',null=True, blank=True) 
    gif=models.FileField(upload_to='reply_gif/',null=True, blank=True) 
    emoji=models.CharField(max_length=10,null=True, blank=True) 
    date_time=models.DateTimeField(auto_now_add=True)    
    def __str__(self):
        return self.text

class Reaction(models.Model):
    comment=models.ForeignKey(Comments, on_delete=models.CASCADE,null=True, blank=True)  
    is_reply=models.IntegerField(default=0) #0 for not reply, 1 for reply
    reply=models.ForeignKey(Reply, on_delete=models.CASCADE,null=True, blank=True)  
    member=models.ForeignKey(Trip_Members, on_delete=models.CASCADE)  
    date_time=models.DateTimeField(auto_now_add=True) 
    is_like=models.IntegerField(default=0) #0 for not liked, 1 for liked,2 for loved,3 for angry,4 for sad
    def __str__(self):
        return self.comment
        
class Reply(models.Model):
    comment = models.ForeignKey(Comments, on_delete=models.CASCADE)  
    reply_by=models.ForeignKey(Trip_Members, on_delete=models.CASCADE)  
    text=models.TextField(null=True, blank=True) 
    image=models.ImageField(upload_to='reply_images/',null=True, blank=True) 
    audio=models.FileField(upload_to='reply_audio/',null=True, blank=True) 
    video=models.FileField(upload_to='reply_video/',null=True, blank=True) 
    gif=models.FileField(upload_to='reply_gif/',null=True, blank=True) 
    emoji=models.CharField(max_length=10,null=True, blank=True) 
    date_time=models.DateTimeField(auto_now_add=True)    
    def __str__(self):
        return self.text
class Rating(models.Model):
    trip_activity = models.ForeignKey(Trip_Activity, on_delete=models.CASCADE)  
    member=models.ForeignKey(Member, on_delete=models.CASCADE)  
    rating=models.IntegerField() 
    def __str__(self):
        return self.rating
class Gallery(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='gallery/',null=True, blank=True) 
    description = models.TextField(null=True, blank=True) 
    def __str__(self):
        return self.trip.title
 
class ExpensesCategory(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField(null=True, blank=True) 
    def __str__(self):
        return self.name
class Expenses(models.Model):
    trip=models.ForeignKey(Trip, on_delete=models.CASCADE)
    expense_category=models.ForeignKey(ExpensesCategory, on_delete=models.CASCADE)
    amount=models.FloatField()
    description=models.TextField(null=True, blank=True) 
    def __str__(self):
        return self.expense_category.name

