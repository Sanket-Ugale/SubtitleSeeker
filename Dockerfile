# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory in the container
WORKDIR /SubtitleSeeker

# Copy the local requirements file to the container
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade setuptools wheel
RUN pip install --no-cache-dir celery==5.3.6
RUN pip install django
# Install any needed packages specified in requirements.txt
# RUN python -m pip install --upgrade pip==21.3.1 && pip install --no-cache-dir -r requirements.txt
RUN python -m pip install --upgrade pip==21.3.1
RUN pip install --no-cache-dir -r requirements.txt
# Copy the current directory contents into the container at /app
COPY . /SubtitleSeeker/

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV NAME World

# ... (previous content)

# Run app.py when the container launches
CMD ["bash", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000 & celery -A subtitlesApp.celery worker --pool=solo -l info"]


# Run app.py when the container launches
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
