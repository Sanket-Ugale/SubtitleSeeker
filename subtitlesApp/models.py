# models.py
from django.db import models

class Subtitle(models.Model):
    title = models.CharField(max_length=255)  # Add max_length to CharField
    description = models.CharField(max_length=1000)  # Adjust max_length as needed
    video = models.CharField(max_length=255)  # Adjust max_length as needed
    subtitle_file = models.CharField(max_length=255)  # Adjust max_length as needed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.video} - Subtitles'