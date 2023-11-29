# Use an official Python runtime as a parent image
FROM python:3.11-slim

ENV APPLE_ID=ryxwaer@gmail.com
ENV PASSWORD=

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the script into the container
COPY icloud_sync.py .

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run sync_script.py when the container launches
CMD ["python", "./icloud_sync.py"]
