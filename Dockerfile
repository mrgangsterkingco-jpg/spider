# Use a lightweight Python version
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (FFmpeg is crucial for yt-dlp to merge video+audio)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 5000
EXPOSE 5000

# Run the app using Gunicorn with a high timeout (300s) for large downloads
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--timeout", "300", "app:app"]
