FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=services.email.app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/ services/

COPY services/email/docker-entrypoint.sh /docker-entrypoint.sh
RUN sed -i 's/\r$//' /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

EXPOSE 5010

RUN useradd -m appuser
USER appuser

ENTRYPOINT ["/docker-entrypoint.sh"]
