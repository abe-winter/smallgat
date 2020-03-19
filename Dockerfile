FROM python:3.8.2

WORKDIR /wheel
# note: this is necessary because (1) scrypt doesn't publish a whl for linux
#   and (2) py slim can't build binaries
RUN pip wheel scrypt==0.8.13

FROM python:3.8.2-slim

WORKDIR /smallgat
COPY requirements.txt .
COPY --from=0 /wheel/./scrypt-0.8.13-cp38-cp38-linux_x86_64.whl .
RUN pip install scrypt-*.whl
RUN pip install -r requirements.txt

COPY smallgat smallgat

CMD gunicorn -b 0.0.0.0:8000 -w 4 smallgat.app:app
