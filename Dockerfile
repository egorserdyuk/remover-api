# Use an official Python runtime as a parent image
FROM python:3.10-alpine

RUN apk update && apk add build-base

RUN apk add cmake make g++

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN python3 -m pip install -r requirements.txt

# Run app.py when the container launches
CMD ["python3", "main.py"]