FROM python:3.8.2-slim

WORKDIR /smallgat
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY smallgat smallgat

CMD gunicorn -b 0.0.0.0:8000 -w 4 smallgat.app:app
