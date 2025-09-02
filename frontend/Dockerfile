# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BACKEND_URL=http://backend:5000

WORKDIR /app
COPY frontend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/app.py ./app.py
COPY frontend/templates ./templates

EXPOSE 3000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:3000", "app:app"]
