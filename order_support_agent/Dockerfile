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

# Run script based on command
CMD ["python", "-c", "import os; cmd = os.getenv('CMD', 'ingest'); exec(open(f'{cmd}_order_data.py').read())"]
ENTRYPOINT ["sh", "-c"]