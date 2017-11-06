"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm

class UploadFileForm(forms.Form):
    file = forms.FileField()