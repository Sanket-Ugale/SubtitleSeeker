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
        videoFile = subtitle_instance.video

        video = videoFile
        with open('temp_file.mp4', 'wb') as temp_file:
            for chunk in video.chunks():
                temp_file.write(chunk)

        video_name = video.name

        sp_list = video_name.split('.')
        video_name_sub = sp_list[0]  # SPLITTING .mp4 from the name

        print('chunkking done ✅')
        subprocess.run(['CCExtractor_win_portable\ccextractorwinfull.exe',
                        'temp_file.mp4', '-o', 'subtitles/'+video_name_sub+'.srt'])  # GETS THE VTT FILE
        # asyncio.run(run_subprocess(['webvtt-to-json', 'subtitles/'+video_name_sub+'.vtt', '-o', 'subtitles/'+video_name_sub+'.json']))
        print('extraction done ✅')
        
        input_path = 'subtitles/'+video_name_sub+'.srt'
        output_path = 'subtitles/'+video_name_sub+'.vtt'
        captions = webvtt.from_srt(input_path)
        captions.save(output_path) #srt to vtt
        print('subtitle done ✅')
        output_json = f'subtitles/{video_name_sub}.json'
        captions = webvtt.read(output_path)
        # Convert captions to a list of dictionaries
        captions_list = [{'start': caption.start_in_seconds, 'end': caption.end_in_seconds, 'text': caption.text} for caption in captions]

        # Save JSON
        with open(output_json, 'w', encoding='utf-8') as json_file:
            json.dump(captions_list, json_file)
        print('Json Conversion done ✅')
        upload_json_to_dynamodb(video_name_sub)#UPLOADING TO DYNAMODB
        print('upload on DB done ✅')
        # video_name = videoFile.name
         # THIS CODE WILL SAVE THE VIDEO IN S3 AND MAKES A PRESIGNED URL FROM IT
        s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                 region_name=AWS_S3_REGION_NAME,)
        default_storage.save(videoFile.name, videoFile)

        print("upload success ✅")

        pre_signed_url_video = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': AWS_STORAGE_BUCKET_NAME,
                'Key': video_name
            },
            ExpiresIn=3600)  # URL expiration time in seconds
        # uploadAndProcessVideo.delay(pre_signed_url_video)
        os.remove('temp_file.mp4')
        os.remove(input_path)
        os.remove(output_path)
        os.remove(output_json)
        return "Video Upload and Processed done Successfully"

    except Subtitle.DoesNotExist:
        return f"Subtitle with ID {id} does not exist."

    except Exception as e:
        return f"An error occurred: {str(e)}"