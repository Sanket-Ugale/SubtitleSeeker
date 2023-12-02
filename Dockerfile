# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory in the container
WORKDIR /SubtitleSeeker

# Copy the local requirements file to the container
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade setuptools wheel
RUN pip install --no-cache-dir celery==5.3.6
RUN pip install django
RUN python -m pip install --upgrade pip==21.3.1
RUN pip install --no-cache-dir -r requirements.txt
COPY . /SubtitleSeeker/
EXPOSE 8000

# Define environment variable
ENV NAME World
CMD ["bash", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000 & celery -A subtitlesApp.celery worker --pool=solo -l info"]