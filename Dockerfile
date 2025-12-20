# Use an appropriate base image with Python pre-installed
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the entire current directory into the container at /app
COPY . /app

# Install any Python dependencies
RUN apt-get update && apt-get install -y tzdata dnsutils iputils-ping && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
ENV TZ="America/New_York"

ARG COMMIT_SHA
ENV COMMIT_SHA=$COMMIT_SHA

# Run Python script
CMD ["python", "main.py"]