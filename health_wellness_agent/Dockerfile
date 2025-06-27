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

# Run script based on command
CMD ["python", "-c", "import os; cmd = os.getenv('CMD', 'ingest'); exec(open(f'{cmd}_health_data.py').read())"]
ENTRYPOINT ["sh", "-c"]