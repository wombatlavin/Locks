from django import forms
from django.forms import ModelForm

from models import Contact, ContactImage

class PhotoContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        exclude = ['id',]
        widgets = {
            'name' : forms.TextInput(attrs={'placeholder' : "Your Name",
                                            'class' : 'form-control',
                                            'required' : 'True'}),
            'email' : forms.EmailInput(attrs={"placeholder" : "Email",
                                              'class' : 'form-control',
                                              'required' : 'True'}),
            'comments' : forms.Textarea(attrs={"placeholder" : "Please tell us anything you think might be helpful",
                                               'class' : 'form-control',
                                               'required' : 'True'}),
        }
        
class PhotoImageForm(forms.Form):
    image = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                            required = True)
