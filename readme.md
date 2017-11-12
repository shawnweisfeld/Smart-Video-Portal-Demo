# Smart Video Portal Demo

## The Plan
1. Upload video into Azure Media Services
1. Queue for transcoding & indexing
1. Stream video with Azure Media Services 
1. Add closed captioning using indexing
1. Add transcription synchronized to the video
1. Make transcription searchable with Azure Search
1. Translate text transcription to Spanish text (Translator API)
1. Allow user to switch closed captioning and transcription between languages
1. Convert Spanish text to audio (Speech API)
1. Content Moderation using Content Moderator API Cognitive Services


## Resources

### Azure Media Services & Cognitive Services
1. [Azure Media Services – On-demand Streaming Learning Path](https://azure.microsoft.com/en-gb/documentation/learning-paths/media-services-streaming-on-demand/)
1. [Translator API](https://docs.microsoft.com/en-us/azure/cognitive-services/translator/translator-info-overview)
1. [Speech API](https://docs.microsoft.com/en-us/azure/cognitive-services/speech/home)
1. [Content Moderation API](https://docs.microsoft.com/en-us/azure/cognitive-services/content-moderator/overview)

### Python & Azure App Service (using Linux containers)
1. [Python Developer Center](https://azure.microsoft.com/en-us/develop/python/)
1. [Use a custom Docker image for Web App for Containers](https://docs.microsoft.com/en-us/azure/app-service/containers/tutorial-custom-docker-image)
1. [Continuous deployment with Web App for Containers](https://docs.microsoft.com/en-us/azure/app-service/containers/app-service-linux-ci-cd)

## Prerequisites

1. [Windows Subsystem for Linux](https://msdn.microsoft.com/en-us/commandline/wsl/install-win10)
1. [Docker Community Edition for Windows](https://store.docker.com/editions/community/docker-ce-desktop-windows)
1. [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest#install-on-debianubuntu-with-apt-get) 
1. Azure Account: you can get a free one [here](https://azure.microsoft.com/en-us/free/)

## The Process

### Create a Django container locally

1. Clone the sample app from GitHub

    ```bash
    git clone https://github.com/Azure-Samples/docker-django-webapp-linux.git --config core.autocrlf=input
    cd docker-django-webapp-linux
    ```

1. Connect Docker in the Linux subsystem to Docker running on the Windows Host

    1. Right click on the docker icon in the system tray, select settings
    1. On the general tab, check the box to `expose the daemon without TLS`
    1. Execute the following command

        ```bash
        export DOCKER_HOST=tcp://127.0.0.1:2375
        ```

1. Build the image from the `Docker` file

    ```bash
    docker build --tag <docker-id>/smartvideoportal:v1.0.0 .
    ```

1. You can now run it locally with the following command

    ```bash
    docker run -d -p 2222:8000 <docker-id>/smartvideoportal:v1.0.0
    ```

1. Open a browser to [http://localhost:2222](http://localhost:2222) and view your handywork

### Push your Django container to Docker Hub

1. Login to Docker Hub

    ```bash
    docker login --username <docker-id> --password <docker-hub-password>
    ```

1. Push the container to the registry

    ```bash
    docker push <docker-id>/smartvideoportal:v1.0.0
    ```

### Deploy to Azure AppService

1. In a Web Browser Login to the [Azure Portal](https://portal.azure.com)
1. We will also like to work with Azure via the console so that we can automate things, so lets also login via the CLI.

    ```bash
    az login
    ```

    > The CLI will prompt you to open a web browser to [https://aka.ms/devicelogin](https://aka.ms/devicelogin) and enter a code. 

1. Lets take a look at all the subscriptions that we have access to with this account. If you have more than one ensure that the one you want to use today is set to default.

    ```bash
    az account list -o table
    ```

1. If the wrong subscrption is selected you can change it like this

    ```bash
    az account set -s 'My Subscription Name'
    ```

1. Create an Azure Resource Group to deploy our app into

    ```bash
    az group create --name svpdResourceGroup --location "South Central US"
    ```

1. Create an App Service Plan to deploy our app into

    ```bash
    az appservice plan create --name svpdAppServicePlan --resource-group svpdResourceGroup --sku S1 --is-linux
    ```

1. Create a Web App and deploy our container into it

    ```bash
    az webapp create --resource-group svpdResourceGroup --plan svpdAppServicePlan --name sweisfel-svpd --deployment-container-image-name <docker-ID>/smartvideoportal:v1.0.0
    ```

    > NOTE: the name of your web app must be globally unique. For demo purposes I put my name in mine.
    > After the above command completes it might take a min or so for your container to spin up and start accepting web requests

1. We can now open our web app in the browser, but we will need to know the default host name, you can get it from the json output from the prior setp or by running the following command.

    ```bash
    az webapp list --resource-group svpdResourceGroup -o table
    ```

### Lets Setup Continuous deployment from our Docker Hub Account to Azue Webapp

1. Every time we publish a new container to Docker Hub, we want Azure to be notified so that it can get it. Start by turning this feature on.

    ```bash
    az webapp deployment container config --resource-group svpdResourceGroup --name sweisfel-svpd -e true
    ```

1. In the json result from the last command you should see your webhook url, if you missed it you can obtain it with this command.

    ```bash
    az webapp deployment container show-cd-url --resource-group svpdResourceGroup --name sweisfel-svpd
    ```

1. In Docker Hub, find the repository that our container is in.
1. Then click on the "Webhooks" menu.
1. Then press the + to create a new one
1. Name it `Smart Video Portal App Service` and paste in the URL we got from Azure

### Lets make a small change to our application, build a new container, test it locally, push the container to docker hub, and then test it in Azure

1. Open up the static index page it is located here: \app\templates\app\index.html
1. Replace the tag line "Build, deploy and scale applications faster" on line 23 with "I Love Azure" and save the file
1. Build the container

    ```bash
    docker build --tag <docker-id>/smartvideoportal:v1.0.0 .
    ```

1. Run the following command to test the container locally, then view it in the browser at [http://localhost:2222](http://localhost:2222)

    ```bash
    docker run -d -p 2222:8000 <docker-id>/smartvideoportal:v1.0.0
    ```

1. Push the container to Docker Hub, within a few minutes you should see your changes on your Azure WebApp   

    ```bash
    docker push <docker-id>/smartvideoportal:v1.0.0
    ```

### Local Development with your Docker Container

1. Turn on "Shared Drives" in your Docker Settings (right click on the docker logo in the system tray)
1. Create a Dev version of your docker file that doesn't copy our application into the container. It should look like [this](https://github.com/shawnweisfeld/Smart-Video-Portal-Demo/blob/master/Dev.Dockerfile).
1. Create a dev.env key=value file to inject your environment variables into the container during local runs.
1. Build the container

    ```bash
    docker build --tag smartvideoportaldev -f Dev.Dockerfile . 
    ```

    > note that we using the `-f` flag to point to the dev version of the dockerfile

1. Run the following command to test the container locally, then view it in the browser at [http://localhost:2222](http://localhost:2222)

    ```bash
    docker run -d -p 2222:8000 -v //c/Users/sweisfel/<path to your code>:/code --env-file dev.env smartvideoportaldev
    ```

    > note that we are telling docker to "mount" our windows drive inside the container. This means that any code changes we make are immidiatly available.
        
### Lets upload our video to Azure Blob storage

1. Create a storage account to store our video

    ```bash
    az storage account create -n svpdstorageaccount -g svpdResourceGroup -l "South Central US" --sku Standard_LRS
    ```

1. Get the admin key for our storage account. Azure creates 2 keys a primary and a secondary allowing for seamless key rotations. 

    ```bash
    az storage account keys list -n svpdstorageaccount -g svpdResourceGroup
    ```

1. Create a storage container to place our uploaded video

    ```bash
    az storage container create -n uploadedvideo --account-name svpdstorageaccount --account-key YOURKEY
    ```

1. Create a storage queue to list videos ready to go to Azure Media Services

    ```bash
    az storage queue create -n videos-to-encode --account-name svpdstorageaccount --account-key YOURKEY
    ```

1. Now we can use the Azure Storage python SDK to upload our file to storage. [More Info](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-python-how-to-use-blob-storage)

    ```python
    block_blob_service = BlockBlobService(account_name=os.environ['SVPD_STORAGE_ACCOUNT_NAME'], account_key=os.environ['SVPD_STORAGE_ACCOUNT_KEY'])
    block_blob_service.create_blob_from_bytes(os.environ['SVPD_STORAGE_ACCOUNT_UPLOADED'], myfile.name, myfile.read())
    ```

1. Next lets toss a message into a storage queue saying that our video is uploaded and ready for processing. [More Info](https://docs.microsoft.com/en-us/azure/storage/queues/storage-python-how-to-use-queue-storage)    

    ```python
    queue_service = QueueService(account_name=os.environ['SVPD_STORAGE_ACCOUNT_NAME'], account_key=os.environ['SVPD_STORAGE_ACCOUNT_KEY'])
    queue_service.put_message(os.environ['SVPD_STORAGE_ACCOUNT_READY_TO_ENCODE'], filename)    
    ```

### Lets send the video we uploaded to Azure Media Services

1. Lets Create the media services account with the portal. [Instructions Here](https://docs.microsoft.com/en-us/azure/media-services/media-services-portal-create-account)
    1. Be sure to create it in the same resource group we created earlier
    1. Be sure that we tie it to the storage account we created earlier
    1. i named mine svpdmediasvc

1. Lets create a service principal for our python app to use to access AMS [Instructions Here](https://docs.microsoft.com/en-us/azure/media-services/media-services-portal-get-started-with-aad#service-principal-authentication)
    1. The 'Connect to Azure Media Services API' option us under 'API access' in the portal.
    1. Be sure to 'create a new' Azure AD application, I called mine smart-video-portal-demo
    1. After you create the application create a client secret
        1. Click 'Manage application'
        1. Then 'keys' on the settings blade
        1. Give your key a description, i called mine webappclient01
        1. Give your key an expiration, i set mine to never (not recommened for real)
        1. Press Save
    1. Copy these 5 values into your dev.env config file
        1. the client secret that we just generated (AMS_CLIENT_SECRET)
        1. the application id (aka client id) off of the registered app blade (AMS_CLIENT_ID)
        1. the three values from the 'connect to media services api' blade 
            1. Azure AD Tenant domain (AZURE_AD_TENANT_DOMAIN)
            1. REST API endpoint (AMS_API_ENDPOINT)
            1. Media Services Resource (AMS_RESOURCE)
    1. Add an additional environment variable for the STS endpoint AZURE_AD_STS=https://login.microsoftonline.com/<AZURE_AD_TENANT_DOMAIN>/oauth2/token
    1. While we are still in the Azure portal lets start our streaming endpoint. [More Info](https://docs.microsoft.com/en-us/azure/media-services/media-services-streaming-endpoints-overview)
    
1. Now we can use the AMS Rest endpoint to render our Adaptive Streaming and Closed Captioning files. [REST API Docs](https://docs.microsoft.com/en-us/rest/api/media/operations/azure-media-services-rest-api-reference)
    1. First we will need to Authenticate agaist the AMS API, we can do that with the following

        ```python
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
        ```

    1. Next, we will need to be able to post data to AMS

        ```python
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
        ```

    1. Finally, we will need to do a 'verbose' post against AMS. This is the same as the above post request, with a two different http headers

        ```python
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
        ```

    1. With the helper methods out of the way we can now, process the video. The process is:
        1. Do we have a video in the queue to get processed?
        1. Authenticate against AMS
        1. Create an Asset to hold our Asset Files
        1. Create an Asset File to hold our video file
        1. Copy the video from the upload location into the container created by the Asset
        1. Create a job with two tasks to process the file
            1. The first task transcodes the video for adaptive streaming
            1. The second task indexes the video converting the spoken text to a closed captioning file
        1. Finally we mark the message in the queue as processed, thus removing it from the queue

            ```python
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

                queue_service.delete_message(os.environ['SVPD_STORAGE_ACCOUNT_READY_TO_ENCODE'], message.id, message.pop_receipt)   
            ```

### Next we need to monitor for the job to complete and then collect the output files

> NOTE: there are many ways to do this, I am [polling](https://docs.microsoft.com/en-us/azure/media-services/media-services-rest-check-job-progress) the job status, but you could also have [AMS send notififications to a queue](https://docs.microsoft.com/en-us/azure/media-services/media-services-dotnet-check-job-progress-with-queues) or to a [WebHook](https://docs.microsoft.com/en-us/azure/media-services/media-services-dotnet-check-job-progress-with-webhooks) 

1. The first step is to create a new queue that we can monitor listing videos getting processed. 

    ```bash
    az storage queue create -n videos-encoding --account-name svpdstorageaccount --account-key YOURKEY
    ```

1. With our new queue created we can now add some code before we delete the videos-to-encode message to insert a videos-encoding message

    ```python
    queue_service.put_message(os.environ['SVPD_STORAGE_ACCOUNT_ENCODING'], json.dumps({ 
        'filename': message_obj['filename'],
        'folder': message_obj['folder'],
        'size': message_obj['size'],
        'job': job['d']}))    
    ```

1. We will need another helper method to Get information from AMS

    ```python
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
    ```

1. And a helper method to delete something from AMS

    ```python
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
    ```

1. Next we need to get the assets from the renderer ready for our media player. This process takes a few steps
    1. Get the message from the queue. Note when we get the message we set its timeout to a minute. So if the job is not complete we will not see the message in the queue again for another minute. 
    1. Assumign we have a message, is the job it references finished rendering?
    1. If so lets consolidate our output assets in one folder, and get rid of the other two
    1. Finally we create a locator, this provides a public URL that we can put in the [AMS player](http://ampdemo.azureedge.net) for our video so people can watch it. 

    Here is my code to the above:

    ```python
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

                    #remove the message from the queue
                    queue_service.delete_message(os.environ['SVPD_STORAGE_ACCOUNT_ENCODING'], message.id, message.pop_receipt)   

            return HttpResponse(template.render({
                'vidstatus': vidstatus,
                'vtt_uri': vtt_uri,
                'ism_uri': ism_uri
            }, request))
    ```

### Now we need to save our rendered video/vtt URLs somewhere and display the videos in our web app

> NOTE: I am going to use [Cosmos DB](https://docs.microsoft.com/en-us/azure/cosmos-db/create-documentdb-python) our NoSQL Store, however you can also use a traditional relational database like [SQL Azure](https://docs.microsoft.com/en-us/azure/sql-database/).

1. Create the CosmosDB account, be sure to capture the document endpoint from the json response from Azure into your env settings

    ```bash
    az cosmosdb create -n svpdsweisfeldb -g svpdResourceGroup
    ```

1. Next you will need to get the keys for the account we just created, and copy the primary master key into our env settings

    ```bash
    az cosmosdb list-keys -n svpdsweisfeldb -g svpdResourceGroup
    ```

1. Next we will need a helper method to create/get a reference to the database

    ```python
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
    ```

1. We will also need a similar helper for the collection 

    ```python
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
    ```

1. Finally a helper to execute a SQL query against cosmos

    ```python
    def docdb_ExecuteQuery(client, collection, query):
        options = {} 
        options['enableCrossPartitionQuery'] = True

        result_iterable = client.QueryDocuments(collection['_self'], query, options)
        return list(result_iterable)
    ```

1. With the helpers out of the way now before we remove the message from the queue after we do the cleanup after our render is complete, we can add the metadata about the rendered video to the database

    ```python
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
    ```

1. Now we can write a simple page to output the list of all videos in our system

    ```python
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
    ```

    ```html
    <ul>
        {% for video in videos %}
            <li><a href="/video/{{video.id}}/">{{ video.filename }}</a></li>
        {% endfor %}
    </ul>
    ```

1. And finally a page to display a single video

    ```python
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
    ```

    In your head tag

    ```html
    <link href="//amp.azure.net/libs/amp/latest/skins/amp-default/azuremediaplayer.min.css" rel="stylesheet">
    <script src="//amp.azure.net/libs/amp/latest/azuremediaplayer.min.js"></script>
    ```

    in your body

    ```html
    <video id="azuremediaplayer" class="azuremediaplayer amp-default-skin amp-big-play-centered" tabindex="0"></video>

    <script type="text/javascript">
            var myOptions = {
                "nativeControlsForTouch": false,
                controls: true,
                autoplay: true,
                width: "640",
                height: "400",
            }
            myPlayer = amp("azuremediaplayer", myOptions);
            myPlayer.src([
                    {
                            "src": "{{ video.ism_uri }}",
                            "type": "application/vnd.ms-sstr+xml"
                    }
            ],
            [
                    {
                            "src": "{{ video.vtt_uri }}",
                            "srclang": "en",
                            "label": "English",
                            "kind": "captions"
                    }
            ]);
    </script>
    ```

### Our next task is to add a transcription syncronized to the video. 

The majority of this is task is just javascript. However the interesting bit is how to get the current position of the playhead from the Azure Media Services Player. Good news for us they made this super easy as we can attach a event listener to the player asking it to notify us every time the play head moves. Once we grab the time code, we can do whatever interesting things we want with it. More info on the [currentTime method](https://amp.azure.net/libs/amp/latest/docs/index.html#amp.player.currenttime) and the players [addEventListener method](https://amp.azure.net/libs/amp/latest/docs/index.html#amp.player.addeventlistener).

```javascript
myPlayer.addEventListener('timeupdate', function() {
        document.getElementById("currentTime").innerHTML = myPlayer.currentTime();
})
```