import requests
import datetime
import simplejson, urllib
import geocoder

from django.shortcuts import render
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import render_to_string, get_template

from forms import PhotoContactForm, PhotoImageForm
from ctl.booking.forms import PostCodeForm
from settings import EMAIL_HOST_USER
from models import Item, MyUser, Job, ContactImage, Review

from schedule.models.events import Event

from ctl.booking.views import booking4

def home(request):
    if 'qwerty' in request.session and 'slot' in request.session and 'date' in request.session and 'contractor_id' in request.session:
        return booking4(request, slot=request.session['slot'], date=request.session['date'], contractor_id=request.session['contractor_id'])

    variables = {}
    variables['form'] = PostCodeForm()
    variables['reviews'] = Review.objects.all()[:3]
    return render(request, 'ctl/index.html', variables)

def tandc(request):
    return render(request,'ctl/tandc.html')

def send_photo(request):
    form = PhotoContactForm()
    imageForm = PhotoImageForm()

    if request.method == 'POST':
        form = PhotoContactForm(request.POST, request.FILES)
        imageForm = PhotoImageForm(request.POST, request.FILES)
        if form.is_valid() and imageForm.is_valid():
            #here we send an email or save the record or something
            contact = form.save()
            
            
            files = request.FILES.getlist('image')
            for f in files:
                m = ContactImage (
                    image = f,
                    contact = contact
                )
                m.save()
            else : print imageForm.errors
            
            
            messages.success(request, "Message sent.  We'll be in contact as soon as we possible.")

            email_body_template = 'contact/photo_email.txt'
            email_subject_template = 'contact/photo_email_subject.txt'
            context = Context()

            context = {}
            context['name'] = contact.name
            context['email'] = contact.email
            context['comment'] = contact.comments

            subject = render_to_string(email_subject_template, context)
            # Force subject to a single line to avoid header-injection
            # issues.
            subject = ''.join(subject.splitlines())
            message = render_to_string(email_body_template,
                                       context)
            email = EmailMessage(subject,
                                 message,
                                 to=[EMAIL_HOST_USER])
            email.send()


    variables = {}
    variables['form'] = form
    variables['imageForm'] = imageForm

    return render(request, 'ctl/contact-form.html', variables)

def cancel(request):
    try: del request.session['qwerty']
    except: pass
    try: del request.session['slot']
    except: pass
    try: del request.session['date']
    except: pass
    try: del request.session['contractor_id']
    except: pass

    return home(request)