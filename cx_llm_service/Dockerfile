FROM python:3.12.4-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get upgrade -y
RUN apt-get install less emacs nano vim zip unzip curl wget jq gcc libldap2-dev libsasl2-dev -y
RUN mkdir -p /app
WORKDIR /app
COPY . /app
RUN pip3 install -r requirements.txt
EXPOSE 5000
CMD python app.py

