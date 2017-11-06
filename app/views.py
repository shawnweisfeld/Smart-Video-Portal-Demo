"""
Definition of views.
"""
import os
from django.template import loader
from django.shortcuts import render
from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponse
from django.template import RequestContext
from datetime import datetime
from azure.storage.blob import BlockBlobService
from .forms import UploadFileForm

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/index.html',
        {
            'title':'Home Page',
            'year':datetime.now().year,
        }
    )

def upload_file(request):
    template = loader.get_template('app/upload_file.html')

    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']

        # save the file to Azure Storage
        block_blob_service = BlockBlobService(account_name=os.environ['SVPD_STORAGE_ACCOUNT_NAME'], account_key=os.environ['SVPD_STORAGE_ACCOUNT_KEY'])
        block_blob_service.create_blob_from_bytes(os.environ['SVPD_STORAGE_ACCOUNT_UPLOADED'], myfile.name, myfile.read())

        return HttpResponse(template.render({
            'uploaded_file_name': myfile.name,
        }, request))

    return HttpResponse(template.render({ }, request))
