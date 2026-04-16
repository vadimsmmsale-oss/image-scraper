FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    chromium-browser \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

ENV CHROME_BIN=/usr/bin/chromium-browser
ENV PYPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

CMD ["sh", "-c", "python3 app.py"]
