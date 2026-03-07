# Insurance Claims Processing Environment
# OpenEnv Hackathon - Statement 3.1 + Scaler AI Labs

ARG BASE_IMAGE=openenv-base:latest
FROM ${BASE_IMAGE}

# Install dependencies
COPY claims_env/server/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Copy OpenEnv core
COPY src/openenv/core/ /app/src/openenv/core/

# Copy environment code
COPY claims_env/ /app/claims_env/

# Set Python path
ENV PYTHONPATH=/app/src:/app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "claims_env.server.app:app", "--host", "0.0.0.0", "--port", "8000"]
