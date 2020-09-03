FROM python:slim

WORKDIR /scripts

RUN pip install --upgrade pip

ADD requirements.txt ./
RUN pip install -r requirements.txt

ADD ./ ./
RUN pip install -e .

VOLUME /config
VOLUME /output

ENTRYPOINT ["minecraftfunctions"]
