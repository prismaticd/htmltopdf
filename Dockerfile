FROM ubuntu:20.04

EXPOSE 8009
ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /files/

RUN apt-get update \
  && apt-get install -y fontconfig fonts-croscore fonts-crosextra-carlito && fc-cache -fv \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip \
  && apt-get install -y  gconf-service libnss3  \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 libc6 libcairo2 libcups2 libdbus-1-3 \
    libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 \
    libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 \
    ca-certificates libappindicator1 lsb-release xdg-utils wget \
  && rm -rf /var/lib/apt/lists/* && rm -rf /root/.cache/

ENTRYPOINT ["/usr/local/bin/uvicorn", "--host", "0.0.0.0", "--port", "8009", "wsgi:app"]

COPY ./requirements.txt /files/requirements.txt

RUN pip3 install -r requirements.txt && rm -rf /root/.cache/

COPY ./ /files/
ARG PYPPETEER_HOME="/tmp/PYPPETEER_HOME"
