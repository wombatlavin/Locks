import requests
import datetime
import simplejson, urllib
import geocoder
import stripe

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from ctl.models import MyUser, Job, JobImage, Customer, Item, Job_Item
from forms import PhotoForm, SignatureForm
from ctl.settings import STRIPE_API_KEY, STRIPE_CLIENT_ID, STRIPE_PUBLISH_KEY, CHANGE_THE_LOCKS_PERCENTAGE

def my_jobs(request):
    '''
    Provides a list of this contractors future (including today) jobs.
    '''
    variables = {}
    myuser = MyUser.objects.get(user__id=request.user.id)
    variables['jobs'] = myuser.my_jobs();
    return render(request, 'contractor/my-jobs.html', variables)

def job_detail(request, job_id):
    '''
    Provides detail of job selected
    '''
    variables = {}
    job = variables['job'] = Job.objects.get(id=job_id)
    variables['work'] = Job_Item.objects.filter(job=job)
    variables['preimage'] = JobImage.objects.filter(job__id=job_id, stage='pre')
    variables['postimage'] = JobImage.objects.filter(job__id=job_id, stage='post')
    return render(request, 'contractor/job-detail.html', variables)

def change_order(request, job_id):
    variables = {}
    items = variables['items'] = Item.objects.all().order_by('category','cost')
    job = variables['job'] = Job.objects.get(id=job_id)
    
    if request.method == 'POST':
        job_items = Job_Item.objects.filter(job=job)
        for j in job_items: j.delete()
        for item in items:
            print request.POST['item_'+str(item.id)]
            if int(request.POST['item_'+str(item.id)]) > 0:
                j = Job_Item (
                    job=job,
                    item=item,
                    count=int(request.POST['item_'+str(item.id)])
                )
                print j.count
                j.save()
        messages.success(request, 'Order Updated.')
        
    return render(request, 'contractor/change-job.html', variables)

def job_photo (request, job_id):
    '''
    Takes and stores a photo for a job
    '''
    variables = {}
    form_data = {}
    form_data['job'] = variables['job_id'] = job_id
    form = PhotoForm(initial=form_data)
    
    if request.POST:
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Photo successfully added.')
    
    variables['form'] = form
    return render(request, 'contractor/take-photo.html', variables)

def customer_signature(request, job_id):
    '''
    Gets customer sigature, requests final payment
    '''
    variables = {}
    
    job = Job.objects.get(id=job_id)
    form = SignatureForm(instance=job)
    
    if request.POST:
        form = SignatureForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Signature successfully added; Payment taken.')
            
            #now take final payment
            mycustomer = Customer.objects.get(user = job.customer)
            contractor = MyUser.objects.get(user = request.user)
            
            #create customer link for contractor
            token = stripe.Token.create(
                customer=mycustomer.stripe_id,
                stripe_account=contractor.stripe_user_id,
            )
            
            # Create the charge on Stripe's servers - this will charge the user's card
            stripe.api_key = STRIPE_API_KEY
            try:
                charge = stripe.Charge.create(
                    amount=int((job.balance())*100), # amount in cents, again
                    currency="gbp",
                    #customer=mycustomer.stripe_id,
                    source=token.id,
                    description= "Change The Locks",
                    application_fee=int((job.balance())*100*CHANGE_THE_LOCKS_PERCENTAGE/100),
                    stripe_account=contractor.stripe_user_id,
                    )
            except stripe.error.CardError, e:
                # The card has been declined
                variables['e'] = e
                return render(request, 'stripe/payment_declined.html', variables)
            
            # now send user confirmation email
            job.completion_email(request)
            
            
            return job_detail(request, job_id)
    
    variables['form'] = form
    variables['job_id'] = job_id
    variables['job'] = job
    
    return render(request, 'contractor/customer-signature.html', variables)



def authorise(request):
    
    site = 'https://connect.stripe.com/oauth/authorize'
    params = {
        "response_type": "code",
        "scope": "read_write",
        "client_id": STRIPE_CLIENT_ID
    }
  
    # Redirect to Stripe /oauth/authorize endpoint
    url = site + '?' + urllib.urlencode(params)
    return redirect(url)
    '''
    variables = {}
    myuser = MyUser.objects.get(user=request.user)
         
    stripe.api_key = STRIPE_API_KEY
    
    acct = stripe.Account.create (
        country="GB",
        type="standard",
        email=request.user.email
    )

    try:
        stripe_user_id = acct['id']
        # all ok and we save the code
        myuser.stripe_user_id = stripe_user_id
        myuser.save ()
    except:
        #something went wrong so report it
        variables['error'] = acct.json().get('error')
        variables['error_desciption'] = acct.json().get('error_description')
    
    print (acct)
    return render(request, 'stripe/contractor-setup-callback.html', variables)
    '''

@csrf_exempt
def stripe_contractor_callback(request, **kwargs):
    variables = {}
    code = request.GET['code']
    
    data = {
        "grant_type": "authorization_code",
        "client_id": STRIPE_CLIENT_ID,
        "client_secret": STRIPE_API_KEY,
        "code": code
    }

    # Make /oauth/token endpoint POST request
    url = 'https://connect.stripe.com/oauth/token'
    resp = requests.post(url, params=data)
    
    try:
        stripe_user_id = resp.json().get('stripe_user_id')
        # all ok and we save the code
        myuser = MyUser.objects.get(user=request.user)
        myuser.stripe_user_id = stripe_user_id
        myuser.save ()
    except:
        #something went wrong so report it
        variables['error'] = resp.json().get('error')
        variables['error_desciption'] = resp.json().get('error_description')
    
    print (resp.json())
    return render(request, 'stripe/contractor-setup-callback.html', variables)
