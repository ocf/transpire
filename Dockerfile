FROM python:3.11-slim AS transpire

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/*
RUN curl -L "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" -o /usr/local/bin/kubectl \
    && chmod +x /usr/local/bin/kubectl
RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

RUN pip install poetry
RUN poetry config virtualenvs.create false

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install

COPY . .

RUN poetry install
