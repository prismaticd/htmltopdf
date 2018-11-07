FROM ubuntu:18.04

EXPOSE 8009

WORKDIR /files/

RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip \
  && apt-get install -y chromium-browser \
  && rm -rf /var/lib/apt/lists/* && rm -rf /root/.cache/

ENTRYPOINT ["/usr/local/bin/gunicorn", "--bind=0.0.0.0:8009", "wsgi:local_app"]

COPY ./requirements.txt /files/requirements.txt

RUN pip3 install -r requirements.txt && rm -rf /root/.cache/

COPY ./ /files/


