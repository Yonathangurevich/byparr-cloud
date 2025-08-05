# Base image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone BYPARR
RUN git clone https://github.com/ThePhaseless/Byparr.git . \
    && rm -rf .git

# Copy our requirements if exists, otherwise use BYPARR's
COPY requirements.txt requirements.txt 2>/dev/null || cp requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a startup script that handles PORT
RUN echo '#!/bin/bash\n\
export PORT=${PORT:-8191}\n\
echo "Starting BYPARR on port $PORT"\n\
python -m uvicorn main:app --host 0.0.0.0 --port $PORT' > /app/start.sh \
    && chmod +x /app/start.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV USE_HEADLESS=True

# The PORT will be set by Cloud Run
EXPOSE 8191

# Use the startup script
CMD ["/app/start.sh"]
