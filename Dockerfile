FROM python:3.11-slim

# Install system dependencies for Manim and FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    texlive \
    texlive-latex-extra \
    texlive-fonts-extra \
    texlive-latex-recommended \
    dvisvgm \
    libcairo2-dev \
    libxml2-dev \
    libxslt1-dev \
    libpango1.0-dev \
    pkg-config \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Command to run your main video pipeline script
CMD ["python", "video_pipeline/main.py"] 
