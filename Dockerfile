FROM python:3.12.3

WORKDIR /app

COPY project/requirements.txt .
RUN pip install -r requirements.txt

COPY project .
RUN chmod +x /app/entrypoint.sh

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/app/entrypoint.sh"]

CMD gunicorn project.wsgi:application --bind 0.0.0.0:${PORT:-8000}