# Use Python 3.11 as the base image
FROM python:3.11-slim

# Install ffmpeg (needed for audio processing)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy requirements first (Docker caches this layer if requirements don't change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port 8000 (where FastAPI runs)
EXPOSE 8000

# Command to run when the container starts
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]