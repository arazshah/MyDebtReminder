FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for database if needed
RUN mkdir -p /app/data

# Set environment variable for token (will be overridden at runtime)
ENV TELEGRAM_BOT_TOKEN="8218518345:AAHsdvHXHL7x86pXJh3tpYiTGu0M1t0sZeo"

# Run the bot
CMD ["python", "main.py"]
