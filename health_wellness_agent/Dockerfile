FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ingest_health_data.py health_wellness_agent.py health_data.csv .env ./

# Keep container running with a shell
CMD ["tail", "-f", "/dev/null"]