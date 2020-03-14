FROM python:3.8.2

WORKDIR /smallgat
COPY requirements.txt .
RUN pip install -r requirements.txt
