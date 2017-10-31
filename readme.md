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


