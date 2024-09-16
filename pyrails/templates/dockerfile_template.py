dockerfile_template = """# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc

# Copy project requirements file
COPY ./requirements.txt /app/requirements.txt

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Uvicorn will listen on this port
EXPOSE 8080

# Install private dependencies and run uvicorn server
CMD uvicorn main:app --host 0.0.0.0 --port 8080
"""
