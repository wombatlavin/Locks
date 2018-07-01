from django.contrib import admin
from models import Item, MyUser, Category, Contact, Customer, Job, Job_Item, JobImage, ContactImage, Review
from admin_commands.add_coords import add_coords

class MyUserAdmin(admin.ModelAdmin):
      actions = [add_coords,]
 
class ContactImageInline(admin.TabularInline):
    model = ContactImage
    extra = 1
 
class ContactAdmin(admin.ModelAdmin):
    inlines = (ContactImageInline,)
    
admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Item)
admin.site.register(Review)
admin.site.register(Category)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Customer)
admin.site.register(Job)
admin.site.register(Job_Item)
admin.site.register(JobImage)
