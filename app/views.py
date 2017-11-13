"""
Definition of views.
"""
import os, random, string, uuid, datetime, json, http.client, urllib, pydocumentdb
from django.template import loader
from django.shortcuts import render
from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponse
from django.template import RequestContext
from azure.storage.blob import BlockBlobService
from azure.storage.queue import QueueService
from .forms import UploadFileForm
import pydocumentdb.document_client as document_client
import xml.etree.ElementTree as ET

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

########################
##### Azure Media Service helpers
########################
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

def ams_delete_request(access_token, uri):
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

    conn.request("DELETE", requrl.path, '', headers)
    res = conn.getresponse()
    return res.status   

########################
##### Cosmos DB helpers
########################
def docdb_CreateDatabaseIfNotExists(client, id):
    db = ''
    databases = list(client.QueryDatabases({
        "query": "SELECT * FROM r WHERE r.id=@id",
        "parameters": [
            { "name":"@id", "value": id }
        ]
    }))

    if len(databases) > 0:
        db = databases[0]
    else:
        db = client.CreateDatabase({"id": id})
    
    return db

def docdb_CreateCollectionIfNotExists(client, db, id):
    collection = ''
    collections = list(client.QueryCollections(db['_self'], {
        "query": "SELECT * FROM r WHERE r.id=@id",
        "parameters": [
            { "name":"@id", "value": id }
        ]
    }))

    if len(collections) > 0:
        collection = collections[0]
    else:
        collection = client.CreateCollection(db['_self'], { 'id': id }, {
            'offerEnableRUPerMinuteThroughput': True,
            'offerVersion': "V2",
            'offerThroughput': 400
        })

    return collection

def docdb_ExecuteQuery(client, collection, query):
    options = {} 
    options['enableCrossPartitionQuery'] = True

    result_iterable = client.QueryDocuments(collection['_self'], query, options)
    return list(result_iterable)


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

def rendered_video(request):
    ism_uri = ''
    vtt_uri = ''
    template = loader.get_template('app/rendered_video.html')
    vidstatus = 'No Running Job Found.'

    # Get the next message from the queue
    queue_service = QueueService(account_name=os.environ['SVPD_STORAGE_ACCOUNT_NAME'], account_key=os.environ['SVPD_STORAGE_ACCOUNT_KEY'])
    messages = queue_service.get_messages(os.environ['SVPD_STORAGE_ACCOUNT_ENCODING'], num_messages=1, visibility_timeout=1*60)
    
    for message in messages:
        vidstatus = 'Rendering: ' + message.content
        message_obj = json.loads(message.content)

        access_token = ams_authenticate()['access_token']

        # Get the details about the job
        job = ams_get_request(access_token, message_obj['job']['__metadata']['uri'])

        # is it done?
        if job['State'] == 3:
            vidstatus = 'Done Rendering: ' + message.content

            #get a reference to our storage container
            block_blob_service = BlockBlobService(account_name=os.environ['SVPD_STORAGE_ACCOUNT_NAME'], account_key=os.environ['SVPD_STORAGE_ACCOUNT_KEY'])
            
            #get a list of all the input and output assets associated to our job
            input_assets = ams_get_request(access_token, message_obj['job']['InputMediaAssets']['__deferred']['uri'])
            output_assets = ams_get_request(access_token, message_obj['job']['OutputMediaAssets']['__deferred']['uri'])

            #look through the input and output assets to figure out what one is for the indexer and for the Adaptive streaming files        
            index_asset = ''
            stream_asset = ''
            for output_asset in output_assets['value']:
                if output_asset['Name'].endswith('- Indexed'):
                    index_asset = output_asset
                elif output_asset['Name'].endswith('- MES v1.1'):
                    stream_asset = output_asset

            #Get the storage container names for each
            dest_container = urllib.parse.urlparse(stream_asset['Uri']).path[1:]
            src_container = urllib.parse.urlparse(index_asset['Uri']).path[1:]
            
            #loop over the indexer output files copying them to the adaptive streaming container
            src_blobs = block_blob_service.list_blobs(src_container)
            for src_blob in src_blobs:
                block_blob_service.copy_blob(dest_container, src_blob.name, output_asset['Uri'] + '/' + src_blob.name)

            #create the access policy if it doen't exist
            access_policies = ams_get_request(access_token, os.environ['AMS_API_ENDPOINT'] + 'AccessPolicies')
            access_policy_id = ''
            for access_policy in access_policies['value']:
                if access_policy['Name'] == 'StreamingAccessPolicy':
                    access_policy_id = access_policy['Id']

            if access_policy_id == '':
                access_policy = ams_verbose_post_request(access_token, 'AccessPolicies', {
                  'Name': 'StreamingAccessPolicy',
                  'DurationInMinutes': '52594560',
                  'Permissions': '9'
                })
                access_policy_id = access_policy['d']['Id']

            #create the locator
            locator = ams_verbose_post_request(access_token, 'Locators', {
                  'AccessPolicyId': access_policy_id,
                  'AssetId': stream_asset['Id'],
                  'Type': 2
                })

            #get the URLs to the streaming endpoint and the vtt file
            locator_asset_files = ams_get_request(access_token, os.environ['AMS_API_ENDPOINT'] + 'Assets(\'' + locator['d']['AssetId']  + '\')/Files')
            for locator_asset_file in locator_asset_files['value']:
                if locator_asset_file['Name'].endswith('.ism'):
                    ism_uri = locator['d']['Path'] + locator_asset_file['Name'] + '/manifest'
                    vtt_uri = locator['d']['Path'] + message_obj['filename'] + '.vtt'

            #delete the job
            ams_delete_request(access_token, message_obj['job']['__metadata']['uri'])

            #delete the unused assets
            ams_delete_request(access_token, os.environ['AMS_API_ENDPOINT'] + 'Assets(\'' + index_asset['Id'] + '\')')
            ams_delete_request(access_token, os.environ['AMS_API_ENDPOINT'] + 'Assets(\'' + input_assets['value'][0]['Id'] + '\')')

            #add the video to the database
            client = document_client.DocumentClient(os.environ['DOCUMENT_ENDPOINT'], {'masterKey': os.environ['DOCUMENT_KEY']})
            db = docdb_CreateDatabaseIfNotExists(client, 'svpd')
            collection = docdb_CreateCollectionIfNotExists(client, db, 'videos')

            doc = client.CreateDocument(collection['_self'],
            { 
                'id': message_obj['folder'].replace('/', '.'),
                'filename': message_obj['filename'],
                'vtt_uri': vtt_uri,
                'ism_uri': ism_uri
            })

            #remove the message from the queue
            queue_service.delete_message(os.environ['SVPD_STORAGE_ACCOUNT_ENCODING'], message.id, message.pop_receipt)   

    return HttpResponse(template.render({
        'vidstatus': vidstatus,
        'vtt_uri': vtt_uri,
        'ism_uri': ism_uri
    }, request))



def videos(request):
    template = loader.get_template('app/videos.html')

    client = document_client.DocumentClient(os.environ['DOCUMENT_ENDPOINT'], {'masterKey': os.environ['DOCUMENT_KEY']})
    db = docdb_CreateDatabaseIfNotExists(client, 'svpd')
    collection = docdb_CreateCollectionIfNotExists(client, db, 'videos')

    videos = docdb_ExecuteQuery(client, collection, {
        "query": "SELECT videos.id, videos.filename FROM videos",
        "parameters": [ ]
    })
    
    return HttpResponse(template.render({
        'videos': videos
    }, request))

def video(request, id):
    template = loader.get_template('app/video.html')

    client = document_client.DocumentClient(os.environ['DOCUMENT_ENDPOINT'], {'masterKey': os.environ['DOCUMENT_KEY']})
    db = docdb_CreateDatabaseIfNotExists(client, 'svpd')
    collection = docdb_CreateCollectionIfNotExists(client, db, 'videos')

    videos = docdb_ExecuteQuery(client, collection, {
        "query": "SELECT * FROM videos WHERE videos.id=@id",
        "parameters": [
            { "name":"@id", "value": id }
        ]
    })    

    return HttpResponse(template.render({
        'videos': videos
    }, request))    

# http://docs.microsofttranslator.com/text-translate.html

def translate(request):
    template = loader.get_template('app/translate.html')

    fromLangCode = 'en'
    toLangCode = 'es'
    textToTranslate = 'The quick brown fox jumped over the red lazy dog.'

    requrl = urllib.parse.urlparse(os.environ['CS_TRANSLATOR_SVC'] + 'Translate')
    conn = http.client.HTTPSConnection(requrl.netloc)
    
    headers = {
        'Ocp-Apim-Subscription-Key': os.environ['CS_TRANSLATOR_KEY'],
        'cache-control': 'no-cache'
        }

    payload = urllib.parse.urlencode({ 
        'appid': '',
        'text': textToTranslate,
        'from': fromLangCode,
        'to': toLangCode
        })

    conn.request("GET", requrl.path + '?' + payload, '', headers)
    res = conn.getresponse()
    xml = ET.fromstring(res.read().decode("utf-8"))
    translation = xml.text

    return HttpResponse(template.render({
      'fromLangCode': fromLangCode,
      'toLangCode': toLangCode,
      'textToTranslate': textToTranslate,
      'translation': translation
    }, request))    

def speak(request):
    language = 'es'
    text = 'El zorro marrón rápido salta sobre el gran perro rojo.'

    requrl = urllib.parse.urlparse(os.environ['CS_TRANSLATOR_SVC'] + 'Speak')
    conn = http.client.HTTPSConnection(requrl.netloc)
    
    headers = {
        'Ocp-Apim-Subscription-Key': os.environ['CS_TRANSLATOR_KEY'],
        'cache-control': 'no-cache'
        }

    payload = urllib.parse.urlencode({ 
        'appid': '',
        'text': text,
        'language': language,
        'format': 'audio/mp3'
        })

    conn.request("GET", requrl.path + '?' + payload, '', headers)
   
    return HttpResponse(conn.getresponse(), content_type='audio/mpeg')