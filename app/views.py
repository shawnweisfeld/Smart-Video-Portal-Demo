"""
Definition of views.
"""
import os, random, string, uuid, datetime
from django.template import loader
from django.shortcuts import render
from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponse
from django.template import RequestContext
from azure.storage.blob import BlockBlobService
from azure.storage.queue import QueueService
from .forms import UploadFileForm

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/index.html',
        {
            'title':'Home Page',
            'year':datetime.datetime.now().year,
        }
    )

def upload_file(request):
    template = loader.get_template('app/upload_file.html')

    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        filename = datetime.datetime.now().strftime('%Y%m%d/')+str(uuid.uuid4()) + '/' + myfile.name

        # save the file to Azure Storage
        block_blob_service = BlockBlobService(account_name=os.environ['SVPD_STORAGE_ACCOUNT_NAME'], account_key=os.environ['SVPD_STORAGE_ACCOUNT_KEY'])
        block_blob_service.create_blob_from_bytes(os.environ['SVPD_STORAGE_ACCOUNT_UPLOADED'], filename, myfile.read())
        
        # put a message into a queue letting the system know the video is ready for processing
        queue_service = QueueService(account_name=os.environ['SVPD_STORAGE_ACCOUNT_NAME'], account_key=os.environ['SVPD_STORAGE_ACCOUNT_KEY'])
        queue_service.put_message(os.environ['SVPD_STORAGE_ACCOUNT_READY_TO_ENCODE'], filename)

        return HttpResponse(template.render({
            'uploaded_file_name': filename,
        }, request))

    return HttpResponse(template.render({ }, request))

def render_video(request):
    template = loader.get_template('app/render_video.html')
    vidstatus = 'No Video Found.'

    queue_service = QueueService(account_name=os.environ['SVPD_STORAGE_ACCOUNT_NAME'], account_key=os.environ['SVPD_STORAGE_ACCOUNT_KEY'])
    messages = queue_service.get_messages(os.environ['SVPD_STORAGE_ACCOUNT_READY_TO_ENCODE'], num_messages=1, visibility_timeout=5*60)
    
    for message in messages:
        vidstatus = 'Queued for Rendering: ' + message.content
        queue_service.delete_message(os.environ['SVPD_STORAGE_ACCOUNT_READY_TO_ENCODE'], message.id, message.pop_receipt)   

    return HttpResponse(template.render({
        'vidstatus': vidstatus,
    }, request))