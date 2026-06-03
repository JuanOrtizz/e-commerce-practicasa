FROM python

WORKDIR /app

COPY project/requirements.txt .
RUN pip install -r requirements.txt

COPY project .

RUN python manage.py collectstatic --noinput

CMD ["sh", "-c", "python manage.py migrate && gunicorn project.wsgi:application --bind 0.0.0.0:$PORT"]