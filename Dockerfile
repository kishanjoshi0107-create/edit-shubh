FROM python:3.9-slim

# System dependencies updated
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Dependencies install karna
RUN pip install --no-cache-dir -r requirements.txt

# Gunicorn se app chalana
CMD gunicorn --bind 0.0.0.0:$PORT app:app
