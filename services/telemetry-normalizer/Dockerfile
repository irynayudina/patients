FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/telemetry-normalizer/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY services/telemetry-normalizer /app

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

# Copy only requirements and install production dependencies
COPY services/telemetry-normalizer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --from=base /app /app

# Expose port
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

