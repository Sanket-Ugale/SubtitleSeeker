import ast
from decimal import Decimal
import json
import secrets
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
from botocore.exceptions import NoCredentialsError
from django.conf import settings
import uuid

def upload_to_s3(file, bucket_name, object_name=None):
    """Upload a file to an S3 bucket."""
    s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    try:
        s3.upload_fileobj(file, bucket_name, object_name)
    except NoCredentialsError:
        print('Credentials not available')

def home(request):

    if request.method == "POST":
        # title = request.POST.get('video_title')
        # desc = request.POST.get('video_description')
        videoFile = request.FILES.get('video_file')

        # Generate a random string (10 characters) using uuid
        random_string = str(uuid.uuid4())[:10]

        # Append the random string to the video file name
        s3_object_name = f'videos/{random_string}_{videoFile.name}'  # Modify the path as needed

        # Save video file to S3
        s3_bucket_name = AWS_STORAGE_BUCKET_NAME
        upload_to_s3(videoFile, s3_bucket_name, s3_object_name)

        # Save other form data to the Subtitle model

        # Trigger the background task
        uploadAndProcessVideo.delay(s3_object_name)


        return HttpResponse("Video upload and processing started.")
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