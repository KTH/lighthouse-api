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
            
# poetry does not yet work with Python 3.10
RUN wget -q -O - "$@" https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
ENV PATH = "${PATH}:/root/.poetry/bin"
ENV FLASK_APP=run.py

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock
COPY run.py run.py
COPY environment.py environment.py
COPY process.py process.py

RUN poetry install

CMD ["poetry", "run", "flask", "run", "--host=0.0.0.0"]