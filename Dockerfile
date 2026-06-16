# Use an official lightweight Python image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (ffmpeg is required for yt-dlp to process audio/video)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application files into the working directory
COPY . .

# Ensure stale database files are not bundled if they exist in databases/
RUN rm -f databases/chat.db databases/chat_database.db

# Expose the container port
EXPOSE 8080

# Start the application using the Flask server
CMD ["python", "main.py"]
