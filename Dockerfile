FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libc6-dev \
        dpkg-dev \
        make \
        vim \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

ENTRYPOINT ["/bin/bash"]
