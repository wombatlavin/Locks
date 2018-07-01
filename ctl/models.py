from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import datetime
import pytz

from django.core.mail import EmailMessage
from django.template.loader import render_to_string, get_template
from django.template import Context
from django.contrib.sites.shortcuts import get_current_site

import simplejson, urllib
from settings import GOOGLE_MAPS_DIRECTIONS_KEY, TIME_ZONE
from math import radians, cos, sin, asin, sqrt

from schedule.models.calendars import Calendar
from schedule.models.events import Event

class Category (models.Model):
    name = models.CharField (
        verbose_name = 'Category',
        max_length = 15,
    )
    image = models.ImageField (
        verbose_name = "Image File",
        upload_to = 'category',
        blank = True,
        null = True,
    )
    
    def __unicode__(self):
        return u'%s' % (self.name)
    
    
class Item (models.Model):
    name = models.CharField (
        verbose_name = 'Name',
        max_length = 60
    )
    description = models.TextField (
        verbose_name = 'Description',
        blank = True,
        null = True
    )
    cost = models.FloatField (
        verbose_name = "Cost",
        default = 0
    )
    time = models.IntegerField (
        verbose_name = "Installation Time (minutes)",
        default = 60
    )
    image = models.ImageField (
        verbose_name = "Image",
        upload_to = "item_images",
    )
    category = models.ForeignKey(
        Category,
        blank=True,
        null=True,
    )
    
    def __unicode__(self):
        return u'%s | %s' % (self.name, self.category)

class MyUser (models.Model):
    user = models.OneToOneField (User)
    post_code = models.CharField (
        verbose_name = "Post Code",
        max_length = 9
    )
    latitude = models.FloatField (
        verbose_name = "Latitude",
        help_text = "Google Maps calculated field based on Post Code",
        blank = True,
        null = True
    )
    longitude = models.FloatField (
        verbose_name = "Longitude",
        help_text = "Google Maps calculated field based on Post Code",
        blank = True,
        null = True
    )
    contractor = models.BooleanField(
        default = False,
        verbose_name = "Contractor"
    )
    call_out_charge = models.FloatField (
        default = 0,
        verbose_name = "Call Out Charge",
    )
    mileage = models.IntegerField (
        default = 10,
        verbose_name = "Max Travel (kilometers)",
        help_text = "Maximum distance from Post Code to Job Site"
    )
    calendar = models.OneToOneField (
        Calendar,
    )
    stripe_user_id = models.CharField (
        max_length = 255,
        verbose_name = "Stripe Token",
        help_text = "Stripe Token allowing access to contractor's stripe account",
        null=True,
        blank=True,
    )
    
    def __unicode__(self):
        return u'%s' % (self.user.username)
    
    def distance(self, pc):
        url = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins='+self.post_code+'&destinations='+pc+'&key='+GOOGLE_MAPS_DIRECTIONS_KEY
        result = simplejson.load(urllib.urlopen(url))
        return result['rows'][0]['elements'][0]['distance']['value']
    
    def haversine(self, lat, lng):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [self.longitude, self.latitude, lng, lat])
        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        km = 6367 * c
        return km
    
    def checktime(self, slot, date, job_time ):
        ''' checks if contractor has availabity in timeslot and returns start time if they do '''
        if slot == 'morning':
            start_time = datetime.datetime.combine(date, datetime.time(hour=8,minute=00,tzinfo=pytz.UTC))
            end_time = datetime.datetime.combine(date, datetime.time(hour=12,minute=00,tzinfo=pytz.UTC))
        elif slot == 'afternoon' :
            start_time = datetime.datetime.combine(date, datetime.time(hour=12,minute=00,tzinfo=pytz.UTC))
            end_time = datetime.datetime.combine(date, datetime.time(hour=16,minute=00,tzinfo=pytz.UTC))
        else :
            start_time = datetime.datetime.combine(date, datetime.time(hour=16,minute=00,tzinfo=pytz.UTC))
            end_time = datetime.datetime.combine(date, datetime.time(hour=22,minute=00,tzinfo=pytz.UTC))
        events = Event.objects.filter(calendar=self.calendar, start__gte=start_time, start__lte=end_time).order_by('start')
        if len(events) < 1 : return start_time
    
        for e in events:
            time_available = e.start - start_time
            if time_available.total_seconds()/60 > job_time : return start_time
            start_time = e.end
        if (end_time - e.end).total_seconds()/60 > job_time: return start_time
        return 'None'
    
    def my_jobs (self):
        start = datetime.datetime.now().replace(hour=1, minute=00)
        return Job.objects.filter(event__calendar=self.calendar, event__start__gte=start).order_by('event__start')
    
class Customer (models.Model):
    user = models.OneToOneField (User)
    stripe_id = models.CharField (
        max_length = 255,
        verbose_name = 'Stripe Id',
        blank = True,
        null = True
    )
    
    def __unicode__(self):
        return u'%s' % (self.user.username)

class Job (models.Model):
    item = models.ManyToManyField (
        Item,
        through='Job_Item',
        verbose_name = 'Items to be installed',
    )
    customer = models.ForeignKey(
        User,
    )
    event = models.ForeignKey(
        Event,
        null = True,
    )
    housenumber = models.CharField (
        max_length = 30,
        verbose_name = "House number/name",
        blank=True
    )
    street = models.CharField (
        max_length = 30,
        verbose_name = "Street",
        blank=True
    )
    city = models.CharField (
        max_length = 30,
        verbose_name = "City",
        blank=True
    )
    post_code = models.CharField (
        max_length = 10,
        verbose_name = "Post Code",
        blank=True
    )
    signature = models.TextField (
        blank = True
    )
    additional_info = models.TextField (
        blank = True
    )
    deposit = models.FloatField(
        blank=True,
        null=True
    )
    
    def confirmation_email(self, request):
        email_body_template = 'booking/confirmation_email.txt'
        email_subject_template = 'booking/confirmation_email_subject.txt'
        context = Context()
        
        context = {}
        context['id'] = self.id
        context['item'] = self.item.name
        context['start'] = self.event.start
        context['end'] = self.event.end
        context['contractor'] = self.event.calendar.myuser.user.username
        
        context['site'] = get_current_site(request)

        subject = render_to_string(email_subject_template, context)
        # Force subject to a single line to avoid header-injection
        # issues.
        subject = ''.join(subject.splitlines())
        message = render_to_string(email_body_template,
                                   context)
        email = EmailMessage(subject,
                             message,
                             to=[self.customer.email])
        email.send()
        
    def completion_email(self, request):
        email_body_template = 'booking/completion_email.txt'
        email_subject_template = 'booking/completion_email_subject.txt'
        context = Context()
        
        context = {}
        context['id'] = self.id
        context['item'] = self.item.name
        context['start'] = self.event.start
        context['end'] = self.event.end
        context['contractor'] = self.event.calendar.myuser.user.username
        context['final_payment'] = self.balance()
        
        context['site'] = get_current_site(request)

        subject = render_to_string(email_subject_template, context)
        # Force subject to a single line to avoid header-injection
        # issues.
        subject = ''.join(subject.splitlines())
        message = render_to_string(email_body_template,
                                   context)
        email = EmailMessage(subject,
                             message,
                             to=[self.customer.email])
        email.send()
        
    def cost(self):
        j = Job_Item.objects.filter(job=self)
        x = 0
        for i in j:
            x += i.item.cost * i.count
        return x
    
    def balance(self):
        return self.cost() - self.deposit
        
    def item_count(self, item):
        try:
            j = Job_Item.objects.get(job=self, item=item)
            return j.count
        except: return 0

class Job_Item(models.Model):
    job = models.ForeignKey(Job)
    item = models.ForeignKey(Item)
    count = models.IntegerField(default = 0)
    
class JobImage (models.Model):
    job = models.ForeignKey(
        Job
    )
    image = models.ImageField(
        upload_to = 'job_image'
    )
    
    IMAGE_STAGE_OPTIONS = (
        ('pre' , 'Pre'),
        ('post' , 'Post')
    )
    stage = models.CharField(
        max_length = 4,
        choices = IMAGE_STAGE_OPTIONS,
        default = 'Pre'
    )

class Contact (models.Model):
    name = models.CharField(
        max_length = 60,
        verbose_name = 'Customer Name',
    )
    email = models.EmailField (
        verbose_name = 'Customer Email',
    )
    comments = models.TextField(
        verbose_name = 'Customer Comments'
    )
    
class ContactImage (models.Model):
    contact = models.ForeignKey(Contact)
    image = models.ImageField (
        verbose_name = 'Customer Lock',
        upload_to = 'contact'
    )
    
class Review (models.Model):
    stars = models.IntegerField(
        default = 5
    )
    feedback = models.TextField()
    customer = models.CharField(
        max_length = 20,
    )
    priority = models.IntegerField(
        default = 0,
        help_text = "The 3 comments with the lowest number will be selected to show on the home screen"
    )
    
    def __unicode__(self):
        return u'%s | %s | %s'  % (self.stars, self.feedback, self.priority)
    
    
    class Meta:
        ordering =['priority']
    