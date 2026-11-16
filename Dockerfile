FROM node:20-slim AS fe
WORKDIR /fe
COPY frontend/package.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 MSANII_ENV=production MSANII_DB=/data/msanii.db MSANII_UPLOAD_DIR=/data/uploads PORT=5000
WORKDIR /app
ARG WITH_LIBROSA=0
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-audio.txt ./
RUN if [ "$WITH_LIBROSA" = "1" ]; then pip install --no-cache-dir -r requirements-audio.txt; fi && pip install --no-cache-dir -r requirements.txt && useradd -m app && mkdir /data && chown app /data
COPY msanii msanii
COPY manage.py start.sh ./
COPY --from=fe /static static
USER app
VOLUME /data
EXPOSE 5000
CMD ["./start.sh"]
