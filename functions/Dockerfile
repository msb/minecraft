FROM python:3.8-slim

WORKDIR /scripts

RUN pip install --upgrade pip

ADD ./ ./
RUN pip install -e .

VOLUME /config
VOLUME /output
VOLUME /scripts/functions

ENTRYPOINT ["minecraftfunctions"]
