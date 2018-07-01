import requests

def add_coords(modeladmin, request, queryset):
    # Adds Lattitude and Longitude Coordinates based on the Post Code
    
    for q in queryset:
        result = requests.get("http://maps.google.com/maps/api/geocode/json?address=" + q.post_code).json()
        q.latitude = result['results'][0]['geometry']['location']['lat']
        q.longitude = result['results'][0]['geometry']['location']['lng']
        q.save()