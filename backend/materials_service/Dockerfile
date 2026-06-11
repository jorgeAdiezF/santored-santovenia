FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/shared/requirements.txt /app/shared_requirements.txt
COPY backend/materials_service/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/shared_requirements.txt && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY backend/shared/ /app/shared/
COPY backend/materials_service/ /app/

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
