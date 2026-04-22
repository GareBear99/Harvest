# Multi-stage build for minimal image size
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 harvest && \
    mkdir -p /app /data && \
    chown -R harvest:harvest /app /data

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/harvest/.local

# Copy application code
COPY --chown=harvest:harvest . .

# Switch to non-root user
USER harvest

# Add local bin to PATH
ENV PATH=/home/harvest/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Default command
ENTRYPOINT ["python", "cli.py"]
CMD ["info"]
