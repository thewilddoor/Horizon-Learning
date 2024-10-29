# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1  # Prevents Python from writing .pyc files to disk
ENV PYTHONUNBUFFERED=1         # Ensures stdout and stderr are unbuffered

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a directory for the app user
RUN mkdir /app

# Set the working directory to /app
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to /app
COPY . /app/

# Expose the port the app runs on
EXPOSE 5000

# Define environment variables for Flask
ENV FLASK_APP=run.py
ENV FLASK_ENV=production  # Change to 'development' if needed

# Optional: If you have a production server like Gunicorn
# Install Gunicorn if not already in requirements.txt
# RUN pip install gunicorn

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app", "--workers", "4"]
