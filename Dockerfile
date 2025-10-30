# Use an official Python base image, version 3.12
FROM python:3.10

# Define the working directory in the container
WORKDIR /app

# Copy application files into container
COPY . .

# Install dependencies
# (Make sure you have a requirements.txt file at the root of the project containing Flask and any other dependencies)
RUN apt-get update && pip install -r requirements.txt

# Set the environment variable to run the application in production mode
ENV FLASK_ENV=production

ENV PYTHONPATH=.
ENV FLASK_APP=src/app.py
# Commande pour démarrer l'application
CMD ["flask", "run", "--host=0.0.0.0"]
