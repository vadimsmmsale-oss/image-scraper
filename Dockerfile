FROM zenika/alpine-chrome:with-puppeteer

USER root

RUN apk add --no-cache python3 py3-pip

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt --break-system-packages

COPY . .

ENV PYPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

CMD ["python3", "app.py"]
