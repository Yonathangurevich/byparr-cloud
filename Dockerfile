# Base image
FROM python:3.11-slim

# Install system dependencies for Chrome and XVFB
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    # Chrome dependencies
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Clone BYPARR repository
RUN git clone https://github.com/ThePhaseless/Byparr.git .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create startup script
RUN echo '#!/bin/bash\n\
export DISPLAY=:99\n\
Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp &\n\
sleep 2\n\
python main.py' > /app/start.sh && chmod +x /app/start.sh

# Environment variables for Cloud Run
ENV PORT=8191
ENV USE_XVFB=True
ENV USE_HEADLESS=True
ENV CHROME_BINARY_LOCATION=/usr/bin/google-chrome-stable

# Create custom main.py wrapper
RUN echo 'import os\n\
os.environ["PORT"] = str(os.environ.get("PORT", "8191"))\n\
os.environ["CHROME_BINARY_LOCATION"] = "/usr/bin/google-chrome-stable"\n\
\n\
# Import and modify seleniumbase settings\n\
import seleniumbase.config.settings as sb_settings\n\
sb_settings.CHROME_START_ARGS = [\n\
    "--no-sandbox",\n\
    "--disable-setuid-sandbox",\n\
    "--disable-dev-shm-usage",\n\
    "--disable-gpu",\n\
    "--disable-web-security",\n\
    "--disable-features=VizDisplayCompositor",\n\
    "--disable-blink-features=AutomationControlled",\n\
    "--user-data-dir=/tmp/chrome-user-data",\n\
    "--disable-software-rasterizer"\n\
]\n\
\n\
# Import original main\n\
from main import *' > /app/main_wrapper.py

# Expose port
EXPOSE 8191

# Start the application
CMD ["/app/start.sh"]
