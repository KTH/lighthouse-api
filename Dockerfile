FROM python:3.7-alpine

WORKDIR repo

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock
COPY run.py run.py
COPY environment.py environment.py
COPY process.py process.py

RUN apk update && \
    apk upgrade && \
    apk add curl docker libxml2-dev libxslt-dev build-base python3-dev libffi-dev openssl-dev

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
ENV PATH = "${PATH}:/root/.poetry/bin"
ENV FLASK_APP=run.py

RUN poetry install

CMD ["poetry", "run", "flask", "run", "--host=0.0.0.0"]