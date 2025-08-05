# Use Python 3.11 slim
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

# Clone BYPARR repository
RUN git clone https://github.com/ThePhaseless/Byparr.git /tmp/byparr \
    && cp -r /tmp/byparr/* . \
    && rm -rf /tmp/byparr

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a proper startup script
RUN echo '#!/usr/bin/env python3\n\
import os\n\
import sys\n\
\n\
# Set port from environment\n\
PORT = int(os.environ.get("PORT", 8191))\n\
os.environ["PORT"] = str(PORT)\n\
\n\
# Set Chrome options\n\
os.environ["CHROME_ARGS"] = "--no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage --disable-gpu --headless"\n\
\n\
print(f"Starting BYPARR on port {PORT}")\n\
\n\
# Import and run the main app directly\n\
import uvicorn\n\
from main import app\n\
\n\
if __name__ == "__main__":\n\
    uvicorn.run(app, host="0.0.0.0", port=PORT)\n\
' > /app/start_server.py

# Make it executable
RUN chmod +x /app/start_server.py

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV USE_HEADLESS=True

# Expose port (will be overridden by Cloud Run)
EXPOSE 8191

# Run the server
CMD ["python", "/app/start_server.py"]
