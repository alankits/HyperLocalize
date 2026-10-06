# HyperLocalize application image (ADR 0012). Not yet built or tested: Docker is not
# installed on the development laptop (prerequisite P9).
FROM python:3.14-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 hl
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=hl:hl . .
USER hl
ENV PYTHONUNBUFFERED=1 HL_MEDIA_ROOT=/media/hl
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
