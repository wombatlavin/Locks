from django import forms
from django.forms import ModelForm

from localflavor.gb.forms import GBPostcodeField

class PostCodeForm(forms.Form):
    postcode = GBPostcodeField(
        label="",
        widget=forms.TextInput(attrs={'placeholder' : "Enter Your Post Code",
                                      'class' : 'form-control'}))

class AddressForm(forms.Form):
    housenumber = forms.CharField(
        max_length = 30,
        label = '',
        widget=forms.TextInput(attrs={'placeholder' : 'House Number/Name',
                                      'class' : 'form-control'})
    )
    street = forms.CharField(
        max_length = 30,
        label = '',
        widget=forms.TextInput(attrs={'placeholder' : 'Street',
                                      'class' : 'form-control',
                                      'readonly' : 'readonly'})
    )
    city = forms.CharField(
        max_length = 30,
        label = '',
        widget=forms.TextInput(attrs={'placeholder' : 'City',
                                      'class' : 'form-control',
                                      'readonly' : 'readonly'})
    )
    postcode = GBPostcodeField(
        label="",
        widget=forms.TextInput(attrs={'placeholder' : "Enter Your Post Code",
                                      'class' : 'form-control',
                                      'readonly' : 'readonly'})
    )
    additional_info = forms.CharField (
        label="",
        required = False,
        widget=forms.Textarea(attrs={'placeholder' : 'Please provide any additional information which may be useful for this job.',
                                     'class' : 'form-control'})
    )