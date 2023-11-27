import ast
from decimal import Decimal
import json
import subprocess
from django.http import HttpResponse, request
from django.shortcuts import render
import webvtt
from SubtitleSeeker.settings import *
from subtitlesApp.models import Subtitle
from boto3.dynamodb.conditions import Key
import boto3
from subtitlesApp.tasks import uploadAndProcessVideo
import gzip
from django.core.files.storage import default_storage


def home(request):
    if request.method=="POST":
        title=request.POST.get('video_title')
        desc=request.POST.get('video_description')
        videoFile = request.FILES.get('video_file')
        subtitle_instance = Subtitle()
        subtitle_instance.title = title
        subtitle_instance.description = desc
        subtitle_instance.video = videoFile
        subtitle_instance.save()
        uploadAndProcessVideo.delay(subtitle_instance.id)
        return render(request,'index.html')
    else:
        try:
                # Establish DynamoDB connection
            session = boto3.Session(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_S3_REGION_NAME
            )
            dynamodb = session.resource('dynamodb')
            table = dynamodb.Table('videoSubtitles')

            # Example query to retrieve all items in the table
            response = table.scan()

            # Retrieve the items from the response
            items = response['Items']

            organized_data_list = []

            # Iterate through each item and organize the data
            for item in items:
                title = item.get('title')
                subtitles_str = item.get('subtitles', '[]')

                # Convert subtitles data back to a list
                subtitles_list = json.loads(subtitles_str, parse_float=Decimal)

                # Fetching video URL
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_S3_REGION_NAME,
                )

                video_key = title + '.mp4'
                pre_signed_url_video = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': AWS_STORAGE_BUCKET_NAME,
                        'Key': video_key
                    },
                    ExpiresIn=3600
                )

                # Organizing data in a new dictionary
                organized_data = {
                    'title': title,
                    'subtitles': subtitles_list,
                    'video_url': pre_signed_url_video
                }

                # Appending the organized data to the list
                organized_data_list.append(organized_data)
                print(organized_data_list)
            # Returning the list of organized data to the Django view
            return render(request, 'index.html', {"videos":organized_data_list})
        except:
            return render(request,'index.html')
   

def login(request):
    return render(request,'login.html')


# def process_video(request):
#     if request.method=="POST":
#         title=request.POST.get('video_title')
#         desc=request.POST.get('video_description')
#         videoFile = request.FILES.get('video_file')
#         subtitle_instance = Subtitle()
#         subtitle_instance.title = title
#         subtitle_instance.description = desc
#         subtitle_instance.video = videoFile
#         subtitle_instance.save()
#         uploadAndProcessVideo.delay(subtitle_instance.id)
#         return render(request,'index.html')
#     else:
#         print("No Input for ProcessVideo Function")
#         return render(request,'index.html')