FROM python:3.11.4-alpine3.18

COPY src /src
WORKDIR /src

RUN OBJECT_CLONER_VERSION=0.0.1 pip3 install .

CMD /usr/local/bin/kopf run --verbose --all-namespaces --liveness=http://0.0.0.0:8080/healthz -m objectcloner