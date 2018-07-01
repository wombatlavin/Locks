import re
import base64

from django import forms
from django.forms import ModelForm

from ctl.models import JobImage, Job

class PhotoForm(forms.ModelForm):
    class Meta:
        model = JobImage
        exclude = ['id',]
        widgets = {
            'job' : forms.HiddenInput(),
            'image' : forms.FileInput(attrs={'accept': 'image/*;capture=camera',
                                             'onchange': "readURL(this);"}),
            'stage' : forms.Select(attrs={'class' : 'form-control'}),
        }
        
class SignatureForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['id','signature']
        widgets = {
            'id' : forms.HiddenInput(),
            'signature' : forms.HiddenInput(),
        }