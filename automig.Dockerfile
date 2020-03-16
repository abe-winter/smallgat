# dockerfile for running migration

FROM python:3.8.2

RUN pip install automig[postgres]==0.0.21
WORKDIR /automig
COPY schema.sql .
COPY .git .
