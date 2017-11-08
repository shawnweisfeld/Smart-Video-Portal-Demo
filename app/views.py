"""
Definition of views.
"""
import os, random, string, uuid, datetime, json, http.client, urllib
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
        folder = datetime.datetime.now().strftime('%Y%m%d/')+str(uuid.uuid4())
        filename = folder + '/' + myfile.name

        # save the file to Azure Storage
        block_blob_service = BlockBlobService(account_name=os.environ['SVPD_STORAGE_ACCOUNT_NAME'], account_key=os.environ['SVPD_STORAGE_ACCOUNT_KEY'])
        block_blob_service.create_blob_from_bytes(os.environ['SVPD_STORAGE_ACCOUNT_UPLOADED'], filename, myfile.read())
        
        # put a message into a queue letting the system know the video is ready for processing
        queue_service = QueueService(account_name=os.environ['SVPD_STORAGE_ACCOUNT_NAME'], account_key=os.environ['SVPD_STORAGE_ACCOUNT_KEY'])
        queue_service.put_message(os.environ['SVPD_STORAGE_ACCOUNT_READY_TO_ENCODE'], json.dumps({ 
            'filename': myfile.name,
            'folder': folder,
            'size': str(myfile.size)}))

        return HttpResponse(template.render({
            'uploaded_file_name': filename,
        }, request))

    return HttpResponse(template.render({ }, request))

def ams_authenticate():
    stsurl = urllib.parse.urlparse(os.environ['AZURE_AD_STS'])
    conn = http.client.HTTPSConnection(stsurl.netloc)
    payload = urllib.parse.urlencode(
        { 'grant_type': 'client_credentials', 
          'client_id': os.environ['AMS_CLIENT_ID'], 
          'client_secret': os.environ['AMS_CLIENT_SECRET'], 
          'resource': os.environ['AMS_RESOURCE'] 
        })

    headers = {
        'content-type': "application/x-www-form-urlencoded",
        'cache-control': "no-cache",
        }

    conn.request("POST", stsurl.path, payload, headers)
    res = conn.getresponse()
    return json.loads(res.read().decode("utf-8"))

def ams_post_request(access_token, path, payload):
    requrl = urllib.parse.urlparse(os.environ['AMS_API_ENDPOINT'] + path)
    conn = http.client.HTTPSConnection(requrl.netloc)

    headers = {
        'x-ms-version': "2.11",
        'accept': "application/json",
        'content-type': "application/json",
        'dataserviceversion': "3.0",
        'maxdataserviceversion': "3.0",
        'authorization': "Bearer " + access_token,
        'cache-control': "no-cache"
        }

    conn.request("POST", requrl.path, json.dumps(payload), headers)
    res = conn.getresponse()
    return json.loads(res.read().decode("utf-8"))

def ams_verbose_post_request(access_token, path, payload):
    requrl = urllib.parse.urlparse(os.environ['AMS_API_ENDPOINT'] + path)
    conn = http.client.HTTPSConnection(requrl.netloc)

    headers = {
        'x-ms-version': "2.11",
        'accept': "application/json;odata=verbose",
        'content-type': "application/json;odata=verbose",
        'dataserviceversion': "3.0",
        'maxdataserviceversion': "3.0",
        'authorization': "Bearer " + access_token,
        'cache-control': "no-cache"
        }

    conn.request("POST", requrl.path, json.dumps(payload), headers)
    res = conn.getresponse()
    return json.loads(res.read().decode("utf-8"))   

def ams_get_request(access_token, uri):
    requrl = urllib.parse.urlparse(uri)
    conn = http.client.HTTPSConnection(requrl.netloc)

    headers = {
        'x-ms-version': "2.11",
        'accept': "application/json",
        'content-type': "application/json",
        'dataserviceversion': "3.0",
        'maxdataserviceversion': "3.0",
        'authorization': "Bearer " + access_token,
        'cache-control': "no-cache"
        }

    conn.request("GET", requrl.path, '', headers)
    res = conn.getresponse()
    return json.loads(res.read().decode("utf-8"))     

def render_video(request):
    template = loader.get_template('app/render_video.html')
    vidstatus = 'No Video Found.'

    queue_service = QueueService(account_name=os.environ['SVPD_STORAGE_ACCOUNT_NAME'], account_key=os.environ['SVPD_STORAGE_ACCOUNT_KEY'])
    messages = queue_service.get_messages(os.environ['SVPD_STORAGE_ACCOUNT_READY_TO_ENCODE'], num_messages=1, visibility_timeout=1*60)
    
    for message in messages:
        vidstatus = 'Queued for Rendering: ' + message.content
        message_obj = json.loads(message.content)

        access_token = ams_authenticate()['access_token']
        
        asset = ams_post_request(access_token, "Assets", {
            'Name': message_obj['filename'], 
            'AlternateId': message_obj['folder']})
        
        asset_container = urllib.parse.urlparse(asset['Uri']).path[1:]

        asset_file = ams_post_request(access_token, "Files", {
            'IsEncrypted': 'false',
            'IsPrimary': 'false',
            'MimeType': 'video/mp4',
            'ContentFileSize': message_obj['size'],
            'Name': message_obj['filename'],
            'ParentAssetId': asset['Id']})

        block_blob_service = BlockBlobService(account_name=os.environ['SVPD_STORAGE_ACCOUNT_NAME'], account_key=os.environ['SVPD_STORAGE_ACCOUNT_KEY'])
        from_url = block_blob_service.make_blob_url(os.environ['SVPD_STORAGE_ACCOUNT_UPLOADED'], message_obj['folder'] + '/' + message_obj['filename'])
        block_blob_service.copy_blob(asset_container, message_obj['filename'], from_url)

        job = ams_verbose_post_request(access_token, "Jobs", {
            'Name': message_obj['filename'], 
            'InputMediaAssets': [{
                '__metadata': { 'uri': os.environ['AMS_API_ENDPOINT'] + 'Assets(\'' + asset['Id'] + '\')' }
            }],
            'Tasks': [{
                'Name': 'Adaptive Streaming Task',
                'Configuration': 'Adaptive Streaming',
                'MediaProcessorId': 'nb:mpid:UUID:ff4df607-d419-42f0-bc17-a481b1331e56',
                'TaskBody': '<?xml version="1.0" encoding="utf-16"?><taskBody><inputAsset>JobInputAsset(0)</inputAsset><outputAsset assetCreationOptions="0" assetFormatOption="0" assetName="' + message_obj['filename'] + ' - MES v1.1" storageAccountName="' + os.environ['SVPD_STORAGE_ACCOUNT_NAME'] + '">JobOutputAsset(0)</outputAsset></taskBody>'
            },{
                'Name': 'Indexing Task',
                'Configuration': '<?xml version="1.0" encoding="utf-8"?><configuration version="2.0"><input><metadata key="title" value="blah" /></input><settings></settings><features><feature name="ASR"><settings><add key="Language" value="English" /><add key="GenerateAIB" value="False" /><add key="GenerateKeywords" value="True" /><add key="ForceFullCaption" value="False" /><add key="CaptionFormats" value="ttml;sami;webvtt" /></settings></feature></features></configuration>',
                'MediaProcessorId': 'nb:mpid:UUID:233e57fc-36bb-4f6f-8f18-3b662747a9f8',
                'TaskBody': '<?xml version="1.0" encoding="utf-16"?><taskBody><inputAsset>JobInputAsset(0)</inputAsset><outputAsset assetCreationOptions="0" assetFormatOption="0" assetName="' + message_obj['filename'] + ' - Indexed" storageAccountName="' + os.environ['SVPD_STORAGE_ACCOUNT_NAME'] + '">JobOutputAsset(1)</outputAsset></taskBody>'
            }]
            })

        queue_service.put_message(os.environ['SVPD_STORAGE_ACCOUNT_ENCODING'], json.dumps({ 
            'filename': message_obj['filename'],
            'folder': message_obj['folder'],
            'size': message_obj['size'],
            'job': job['d']}))

        queue_service.delete_message(os.environ['SVPD_STORAGE_ACCOUNT_READY_TO_ENCODE'], message.id, message.pop_receipt)   

    return HttpResponse(template.render({
        'vidstatus': vidstatus,
    }, request))