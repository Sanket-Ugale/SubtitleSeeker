# Generated by Django 4.2.7 on 2023-11-25 04:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subtitlesApp", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subtitle",
            name="subtitle_file",
            field=models.FileField(upload_to="static/Subtitles/"),
        ),
        migrations.AlterField(
            model_name="subtitle",
            name="video",
            field=models.FileField(upload_to="static/videos/"),
        ),
    ]
