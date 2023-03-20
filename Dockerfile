FROM python:3.11-alpine AS transpire

RUN apk add git openssh-client
RUN apk add kubectl --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing/
RUN apk add helm --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community/

RUN pip install poetry
RUN poetry config virtualenvs.create false

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev

COPY . .

RUN poetry install --no-dev
