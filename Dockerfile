FROM python:3.8-slim-buster

USER root

RUN useradd -ms /bin/bash customuser

RUN \
  apt-get update && apt-get install -y --no-install-recommends \
  libpq-dev gcc libc-dev

USER customuser

WORKDIR /app

ENV PATH="${PATH}:/home/customuser/.local/bin"

COPY requirements.txt requirements.txt

RUN \
  /usr/local/bin/python3 -m pip install --upgrade pip && \
  pip3 install -r requirements.txt

COPY app .

EXPOSE 8080

ENTRYPOINT [ "python3" ]

CMD [ "back.py" ]
