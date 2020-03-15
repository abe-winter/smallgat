FROM python:3.8.2

WORKDIR /smallgat
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .
COPY util .
COPY templates .
COPY blueprints .

CMD gunicorn -w 4 smallgat.app:app
