FROM python:3.12.3

WORKDIR /app

COPY project/requirements.txt .
RUN pip install -r requirements.txt

COPY project .

CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn project.wsgi:application --bind 0.0.0.0:$PORT"]