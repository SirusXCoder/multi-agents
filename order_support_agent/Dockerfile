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
COPY ingest_order_data.py order_support_agent.py order_data.csv .env ./

# Keep container running with a shell
CMD ["tail", "-f", "/dev/null"]