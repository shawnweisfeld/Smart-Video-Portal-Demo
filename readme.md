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
    1. Add an additional environment variable for the STS endpoint AZURE_AD_STS=https://login.microsoftonline.com/microsoft.onmicrosoft.com/oauth2/token
    
1. Now we can use the AMS Rest endpoint to render our Adaptive Streaming and Closed Captioning files.

### Next we need to monitor for the job to complete and then collect the output files