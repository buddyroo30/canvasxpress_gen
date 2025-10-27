FROM python:3.9.16-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get upgrade -y
RUN apt-get install less emacs nano vim zip unzip curl wget jq gcc libldap2-dev libsasl2-dev -y
RUN apt-get install sqlite3 -y
RUN pip install FlagEmbedding
RUN mkdir -p /app
WORKDIR /app
COPY . /app
RUN pip3 install -r requirements.txt

# Optional development dependencies for testing
ARG INSTALL_DEV=false
RUN if [ "$INSTALL_DEV" = "true" ] ; then pip3 install -r requirements-dev.txt ; fi

RUN pip3 install -e .
EXPOSE 5000
CMD python app.py

