FROM kthse/kth-python:3.10.0

WORKDIR repo

RUN apk update && \
    apk upgrade && \
    apk add  \
            curl \
            docker \
            libxml2-dev \
            libxslt-dev \
            build-base \
            python3-dev \
            libffi-dev \
            openssl-dev \
            rust \
            cargo

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

COPY lighthouse-api.py lighthouse-api.py
COPY environment.py environment.py
COPY process.py process.py

RUN poetry install

CMD FLASK_APP=lighthouse-api.py pipenv run flask run --host=0.0.0.0