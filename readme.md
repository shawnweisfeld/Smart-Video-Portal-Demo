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

1. [Python Developer Center](https://azure.microsoft.com/en-us/develop/python/)
1. [Create a Python web app in Azure](https://docs.microsoft.com/en-us/azure/app-service/app-service-web-get-started-python)
1. [Configuring Python with Azure App Service Web Apps](https://docs.microsoft.com/en-us/azure/app-service/web-sites-python-configure)
1. [Azure Media Services – On-demand Streaming Learning Path](https://azure.microsoft.com/en-gb/documentation/learning-paths/media-services-streaming-on-demand/)
1. [Translator API](https://docs.microsoft.com/en-us/azure/cognitive-services/translator/translator-info-overview)
1. [Speech API](https://docs.microsoft.com/en-us/azure/cognitive-services/speech/home)
1. [Content Moderation API](https://docs.microsoft.com/en-us/azure/cognitive-services/content-moderator/overview)


## Prerequisites

1. [Windows Subsystem for Linux - Install for Windows 10](https://msdn.microsoft.com/en-us/commandline/wsl/install-win10) *if running Windows*
1. [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest#install-on-debianubuntu-with-apt-get) 
1. Azure Account: you can get a free one [here](https://azure.microsoft.com/en-us/free/)

## The Process

### Login and Setup Hello World Python App

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
    az appservice plan create --name svpdAppServicePlan --resource-group svpdResourceGroup --sku FREE
    ```

1. Create a Web App do deploy our app into

    ```bash
    az webapp create --resource-group svpdResourceGroup --plan svpdAppServicePlan --name sweisfel-svpd --runtime "python|3.4"
    ```

    > NOTE: the name of your web app must be globally unique. For demo purposes I put my name in mine.

1. We can now open our web app in the browser, but we will need to know the default host name, you can get it from the json output from the prior setp or by running the following command.

    ```bash
    az webapp show --resource-group svpdResourceGroup --name sweisfel-svpd
    ```

    > You should now see a blue webpage telling you that your site online and setup to run python.

### Lets setup Django for our application

1. Install virtualenv and virtualenvwrapper 

    > Instructions [from](https://askubuntu.com/questions/244641/how-to-set-up-and-use-a-virtual-python-environment-in-ubuntu)

    ```bash
    sudo apt-get install python-virtualenv
    sudo apt install virtualenvwrapper
    echo "source /usr/share/virtualenvwrapper/virtualenvwrapper.sh" >> ~/.bashrc
    ```

1. Setup virtualenv and virtualenvwrapper

    ```bash
    export WORKON_HOME=~/.virtualenvs
    mkdir $WORKON_HOME
    echo "export WORKON_HOME=$WORKON_HOME" >> ~/.bashrc
    echo "export PIP_VIRTUALENV_BASE=$WORKON_HOME" >> ~/.bashrc 
    source ~/.bashrc
    ```

1. Make a virtualenv

    ```bash
    mkvirtualenv --python=/usr/bin/python3 smartvideodemo
    ```

    > NOTE you can leave, come back, and delete your virtualenv with the following commands

    ```bash
    deactivate
    workon smartvideodemo
    rmvirtualenv smartvideodemo
    ```

1. Install Django

    ```bash
    pip install Django 
    ```

1. Create the Django project

    ```bash
    django-admin startproject smartvideo
    ```

1. We can now test our default project is running using the Django webserver. 

    ```bash
    python3 manage.py runserver
    ```

    Now you can open up your web browser and view our project at [http://127.0.0.1:8000/](http://127.0.0.1:8000/)


### Lets Setup Continuous deployment from our Git Repo to Azue Webapp

1. Every time we check code into our master brach on GitHub we want to notify our Azure Webapp. It will then pull our code over, compile it and update our site. 

    ```bash
    az webapp deployment source config --resource-group svpdResourceGroup --name sweisfel-svpd --repo-url https://github.com/shawnweisfeld/Smart-Video-Portal-Demo --branch master --repository-type github --git-token YOURKEY
    ```
    
    > Here we are setting up a super simple deployment, however in the real world we would likely want to deploy to multiple environments with signoffs between each. VisualStudio.com has a great build/release pipeline that can handle these more complex requirements. 

    > Generate the GitHub token [here](https://github.com/settings/tokens). I gave mine the following permissions admin:repo_hook, notifications

1. You should now see our simple hello world app running. Now we have our environment all setup and we can begin adding functionality. 

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

1. 