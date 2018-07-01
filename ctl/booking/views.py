import requests
import datetime
import simplejson, urllib
import geocoder
import stripe

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from forms import PostCodeForm, AddressForm
from ctl.settings import GOOGLE_MAPS_DIRECTIONS_KEY, STRIPE_PUBLISH_KEY, STRIPE_API_KEY, CHANGE_THE_LOCKS_PERCENTAGE, CHANGE_THE_LOCKS_DEPOSIT

from ctl.models import Item, MyUser, Job, Category, Customer, Job_Item


from schedule.models.events import Event

def booking(request):
    '''
    This function identifies the post code is valid and gets the latitude and longitude.
    It checks if we have a contractor in the area and gives work (item) options if we do.
    '''
    variables = {}
    
    # if no form this hasn't been called from home so go there
    try: form = PostCodeForm(request.GET)
    except: return home(request)
    request.session['postcode'] = request.GET['postcode']
    result = requests.get("http://maps.google.com/maps/api/geocode/json?address=" + request.session['postcode']).json()
    try: request.session['latitude'] = result['results'][0]['geometry']['location']['lat']
    except: pass
    try: request.session['longitude'] = result['results'][0]['geometry']['location']['lng']
    except: pass
    
    #check this gives us a valide address
    g = geocoder.google(request.session['postcode'])
    if g.street is None:
        messages.warning(request, 'Cannot find a Street for this postcode.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    if g.city is None:
        messages.warning(request, 'Cannot find a City for this postcode.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    #check for valid post code
    if form.is_valid() :
        #find a contractor in the area
        contractors = MyUser.objects.filter(contractor=True)
        contractor_found = False
        for s in contractors:
            if s.haversine(request.session['latitude'], request.session['longitude']) < s.mileage:
                contractor_found = True
                break
        if not contractor_found: return render(request, 'booking/no-coverage.html', variables)
        
        #provide various options
        variables['items'] = Item.objects.all().order_by('cost')
        variables['categories'] = Category.objects.all()
        variables['menu'] = 'menu2'

        return render(request, 'booking/booking.html', variables)
    
    variables['form'] = form
    return render(request, 'ctl/index.html', variables)

def booking2(request, date=datetime.datetime.now().date()+datetime.timedelta(days=1)):
    '''
    This function checks time availability of contractors in the area and presents timeslot options
    '''
    
    try: start = date = datetime.datetime.strptime(date, '%Y-%m-%d')
    except: start = datetime.datetime.now().date() + datetime.timedelta(days=1)
    end = start + datetime.timedelta(days=1)
    
    try: test = request.session['qwerty']
    except:
        items = Item.objects.all()
        mylist = []
        cost = 0
        site_time = 0
        for item in items:
            if int(request.GET['item_'+str(item.id)]) > 0:
                num = int(request.GET['item_'+str(item.id)])
                mylist.append([item.id, item.name, num, item.cost * num])
                cost += item.cost * num
                site_time += item.time * num
            
        request.session['cost'] = cost
        request.session['qwerty'] = mylist
        request.session['site_time'] = site_time
    variables = {}
    
    #get all available contractors
    contractors = MyUser.objects.filter(contractor=True)
    unsorted_contractors = contractors.all()
    sorted_contractors = sorted(unsorted_contractors, key=lambda t: t.haversine(request.session['latitude'], request.session['longitude']))
    for s in sorted_contractors:
        if s.haversine(request.session['latitude'], request.session['longitude']) > s.mileage:
            i = sorted_contractors.index(s)
            sorted_contractors.pop(i)
            
    availability = ['None', 'None', 'None', 'None', 'None', 'None']

    for s in sorted_contractors:
        url = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins='+request.session['postcode']+'&destinations='+s.post_code+'&key='+GOOGLE_MAPS_DIRECTIONS_KEY
        result = simplejson.load(urllib.urlopen(url))
        travel_time = int(result['rows'][0]['elements'][0]['duration']['value']/60) * 2
        job_time = travel_time + request.session['site_time']
        events = Event.objects.filter(calendar=s.calendar, start__gte=start, start__lte=end).order_by('start')
        if availability[0] == 'None' :
            if s.checktime('morning', start, job_time) != "None": availability[0] = 'Yes'
        if availability[1] == 'None' :
            if  s.checktime('afternoon', start, job_time) != "None" : availability[1] = 'Yes'
        if availability[2] == 'None' :
            if s.checktime('evening', start, job_time) != "None" : availability[2] = 'Yes'
        if availability[3] == 'None' :
            if s.checktime('morning', end, job_time) != "None" : availability[3] = 'Yes'
        if availability[4] == 'None' :
            if s.checktime('afternoon',  end, job_time) != 'None' :availability[4] = 'Yes'
        if availability[5] == 'None' :
            if s.checktime('evening', end, job_time) != 'None' : availability[5] = 'Yes'
        if availability == ['Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes']: break
    
    variables['availability'] = availability
    variables['first_date'] = date
    variables['cost'] = request.session['cost']
    variables['menu'] = 'menu2'
    return render(request, 'booking/booking2.html', variables)

def booking3(request, date, slot):
    '''
    This function gets the site details
    '''
    try: start = date = datetime.datetime.strptime(date, '%Y-%m-%d')
    except: start = date + datetime.timedelta(days=1)
    end = start + datetime.timedelta(days=1)
    
    variables = {}
    
    #get all available contractors
    contractors = MyUser.objects.filter(contractor=True)
    unsorted_contractors = contractors.all()
    sorted_contractors = sorted(unsorted_contractors, key=lambda t: t.haversine(request.session['latitude'], request.session['longitude']))
        
    #find closest contractor with timeslot
    for s in sorted_contractors:
        url = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins='+request.session['postcode']+'&destinations='+s.post_code+'&key='+GOOGLE_MAPS_DIRECTIONS_KEY
        result= simplejson.load(urllib.urlopen(url))
        travel_time = int(result['rows'][0]['elements'][0]['duration']['value']/60) * 2
        job_time = travel_time + request.session['site_time']
        if s.checktime(slot, start, job_time) != "None":
            break
        
    if s.checktime(slot, start, job_time) == "None":
        # timeslot has been lost
        pass
    else : variables['contractor'] = s
    
    #we need to get address from postcode
    g = geocoder.google(request.session['postcode'])
    form_data = {}
    form_data['street'] = g.street
    form_data['city'] = g.city
    form_data['postcode'] = g.postal
    form=AddressForm(initial=form_data)
    
    variables['form'] = form
    variables['date'] = date
    variables['slot'] = slot
    variables['cost'] = request.session['cost']
    variables['menu'] = 'menu2'
    return render(request, 'booking/booking3.html', variables)

def booking4(request, date, slot, contractor_id):
    '''
    This function is for users to confirm
    '''
    variables = {}
    try: start = date = datetime.datetime.strptime(date, '%Y-%m-%d')
    except: start = date + datetime.timedelta(days=1)
    end = start + datetime.timedelta(days=1)
    
    form = AddressForm(request.GET)
    if form.is_valid():
        request.session['address'] = [request.GET['housenumber'], request.GET['street'], request.GET['city'], request.GET['postcode']]
        request.session['additional_info'] = request.GET['additional_info']
    else :
        variables['form'] = form
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    mylist = []
    for item in request.session['qwerty']:
        mylist.append(Item.objects.get(id=item[0]))

    variables['items'] = mylist
    variables['contractor'] = contractor = MyUser.objects.get(id=contractor_id)
    variables['date'] = date
    variables['slot'] = slot
    variables['stripe_key'] = STRIPE_PUBLISH_KEY
    request.session['deposit'] = round(request.session['cost'] * CHANGE_THE_LOCKS_DEPOSIT / 100, 2)
    variables['address'] = request.session['address']
    request.session['slot'] = slot
    request.session['date'] = date.strftime('%Y-%m-%d')
    request.session['contractor_id'] = contractor_id
    variables['cost'] = request.session['cost']
    variables['menu'] = 'menu2'

    return render(request, 'booking/booking4.html', variables)

@csrf_exempt
def booking5(request, date, slot, contractor_id):
    '''
    Actual booking takes place
    '''
    #found first contractor so save it to earliest possible time
    # find first available time
    try: start = date = datetime.datetime.strptime(date, '%Y-%m-%d')
    except: start = date + datetime.timedelta(days=1)
    end = start + datetime.timedelta(days=1)
    contractor = MyUser.objects.get(id=contractor_id)
    
    url = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins='+request.session['postcode']+'&destinations='+contractor.post_code+'&key='+GOOGLE_MAPS_DIRECTIONS_KEY
    result= simplejson.load(urllib.urlopen(url))
    travel_time = int(result['rows'][0]['elements'][0]['duration']['value']/60) * 2
    job_time = travel_time + request.session['site_time']
    
    start_time = contractor.checktime(slot, start, job_time)
    if start_time == 'None':
        #we need to handle the slot being lost
        messages.warning(request, 'Timeslot has been taken since we started the process.  Please select another.')
        return booking2(request)
    
    event = Event (
        start = start_time,
        end = start_time + datetime.timedelta(minutes=job_time),
        title = "Change The Locks: " + request.session['postcode'],
        description = request.session['postcode'],
        calendar = contractor.calendar
    )
    event.save()
    job = Job (
        customer = request.user,
        event = event,
        housenumber = request.session['address'][0],
        street = request.session['address'][1],
        city = request.session['address'][2],
        post_code = request.session['address'][3],
        additional_info = request.session['additional_info'],
        deposit = request.session['deposit']
    )
    job.save()
    for q in request.session['qwerty']:
        try: job_item = Job_Item.objects.get(job=job, item=Item.objects.get(id=q[0]))
        except: job_item = Job_Item(job=job,item=Item.objects.get(id=q[0]))
        job_item.count = q[2]
        job_item.save()
    
    stripe.api_key = STRIPE_API_KEY
    token = request.POST['stripeToken']
    
    try: mycustomer = Customer.objects.get(user=request.user)
    except:
        mycustomer = Customer(
            user=request.user
        )
        mycustomer.save()
    if not mycustomer.stripe_id:
        # create the customer
        customer = stripe.Customer.create(
            email=request.user.email,
            source=token,
        )
        
        # save customer stripe id
        mycustomer.stripe_id = customer.id
        mycustomer.save()
    
    
    #create customer link for contractor
    token = stripe.Token.create(
        customer=mycustomer.stripe_id,
        stripe_account=contractor.stripe_user_id,
    )
    
    # Create the charge on Stripe's servers - this will charge the user's card
    try:
        charge = stripe.Charge.create(
            amount=int(request.session['deposit']*100), # amount in cents, again
            currency="gbp",
            #customer=mycustomer.stripe_id,
            source=token.id,
            description= "Change The Locks",
            application_fee=int((request.session['deposit']*100)*CHANGE_THE_LOCKS_PERCENTAGE/100),
            stripe_account=contractor.stripe_user_id,
            )
    except stripe.error.CardError, e:
        # The card has been declined so clear down the recently added records
        job.delete()
        event.delete()
        job_items = Job_Item.objects.filter(job=job)
        for job_item in job_items: job_item.delete()
        variables['e'] = e
        return render(request, 'stripe/payment_declined.html', variables)
    
    job.confirmation_email(request)
    
    variables = {}
    variables['contractor'] = contractor 
    variables['date'] = date
    variables['slot'] = slot
    variables['address'] = request.session['address']
    variables['job'] = job
    
    del request.session['qwerty']
    del request.session['slot']
    del request.session['contractor_id']
    del request.session['date']
    del request.session['address']
    del request.session['additional_info']
    del request.session['deposit']
    del request.session['site_time']
    variables['menu'] = 'menu2'

    return render(request, 'booking/booking5.html', variables)