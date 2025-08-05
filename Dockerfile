# Use Python slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone BYPARR repository
RUN git clone https://github.com/ThePhaseless/Byparr.git /tmp/byparr \
    && cp -r /tmp/byparr/* . \
    && rm -rf /tmp/byparr

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our Cloud Run wrapper
COPY main_cloudrun.py .

# Set environment variables
ENV PORT=8191
ENV PYTHONUNBUFFERED=1
ENV USE_HEADLESS=True

# Expose port
EXPOSE 8191

# Run the application
CMD ["python", "main_cloudrun.py"]
