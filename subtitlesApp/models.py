# models.py
from django.db import models

class Subtitle(models.Model):
    title=models.CharField(max_length=100)
    description=models.CharField(max_length=600)
    video = models.FileField(upload_to='')
    subtitle_file = models.FileField(upload_to='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.video.name} - Subtitles'