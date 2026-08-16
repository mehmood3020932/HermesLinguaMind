FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-phase3.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy shared modules
COPY shared/ /app/shared/

# Copy service code
COPY services/coin_ledger/main.py /app/main.py

# Create non-root user
RUN useradd -m -u 1000 hermes && chown -R hermes:hermes /app
USER hermes

EXPOSE 8006

CMD ["python", "main.py"]
