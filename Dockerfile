FROM python:3.8-slim-buster

USER root

RUN useradd -ms /bin/bash customuser

RUN \
  apt-get update && \
  apt-get install -y libpq-dev gcc python3-psycopg2 && \
  apt-get clean

USER customuser

WORKDIR /app

ENV PYTHONUNBUFFERED=1

ENV VIRTUAL_ENV=/home/customuser/venv

RUN python3 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .

RUN \
  /usr/local/bin/python3 -m pip install --upgrade pip && \
  pip --no-cache-dir install -r requirements.txt

COPY app .

EXPOSE 8080

ENTRYPOINT [ "python3" ]

CMD [ "back.py" ]
