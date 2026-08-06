FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# Build context is the repo root (see docker-compose.yml / render.yaml), not backend/, so the
# frontend files below are reachable alongside the API source.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY index.html ./index.html
COPY css ./css
COPY js ./js
COPY pages ./pages
COPY admin ./admin
COPY images ./images
EXPOSE 8000
# $PORT is set by Render (and similar platforms) at runtime; default to 8000 for plain
# `docker run`/docker-compose use. Shell form so the variable actually expands.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
