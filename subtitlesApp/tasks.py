from decimal import Decimal
import json
from celery import shared_task
from SubtitleSeeker.settings import *
from .models import Subtitle
import subprocess
import webvtt
from django.core.files.storage import default_storage
import boto3


@shared_task
def upload_json_to_dynamodb(video_name_sub):
    with open('subtitles/' + video_name_sub + '.json', 'r') as json_file:
        subtitles_data = json.load(json_file)

    # Establish DynamoDB connection
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_S3_REGION_NAME
    )
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table('videoSubtitles')

    # Prepare data for insertion
    title = video_name_sub
    subtitles = json.dumps(subtitles_data, default=lambda x: str(x) if isinstance(x, Decimal) else x)

    item = {
        'title': title,
        'subtitles': subtitles
    }

    # Insert data into DynamoDB
    response = table.put_item(Item=item)
    print('✅done uploading to DynamoDB:', response)


@shared_task(bind=True)
def uploadAndProcessVideo(self, id):
    try:
        # Get Subtitle instance for the given ID
        subtitle_instance = Subtitle.objects.get(id=id)
        video_name = subtitle_instance.video.name

        # Download the video file from S3
        s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                 region_name=settings.AWS_S3_REGION_NAME)

        # Use a unique name for the temporary video file
        temp_video_name = f'temp_video_{id}.mp4'

        with open(temp_video_name, 'wb') as temp_file:
            s3_client.download_fileobj(settings.AWS_STORAGE_BUCKET_NAME, video_name, temp_file)

        print('Downloaded video from S3 ✅')

        # Rest of your processing code remains unchanged
        sp_list = video_name.split('.')
        video_name_sub = sp_list[0]  # SPLITTING .mp4 from the name
        # ... (rest of your processing code)

        # Upload the processed video back to S3
        processed_video_name = f'processed_video_{id}.mp4'
        with open(temp_video_name, 'rb') as processed_video:
            s3_client.upload_fileobj(processed_video, settings.AWS_STORAGE_BUCKET_NAME, processed_video_name)

        print('Processed video uploaded to S3 ✅')

        # Clean up temporary files
        os.remove(temp_video_name)
        # ... (rest of your cleanup code)

        # Delete the original video file from S3 after processing
        s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=video_name)

        # Delete processed subtitle files from S3
        s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=f'subtitles/{video_name_sub}.srt')
        s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=f'subtitles/{video_name_sub}.vtt')
        s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=f'subtitles/{video_name_sub}.json')

        return "Video Upload and Processed done Successfully"

    except Exception as e:
        print(f"Error: {e}")
        return "Error processing video"

    except Subtitle.DoesNotExist:
        return f"Subtitle with ID {id} does not exist."

    except Exception as e:
        return f"An error occurred: {str(e)}"