FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc=4:12.2.0-3 \
        g++=4:12.2.0-3 \
        libc6-dev=2.36-9+deb12u14 \
        dpkg-dev=1.21.23 \
        make=4.3-4.1 \
        vim=2:9.0.1378-2+deb12u2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app
RUN pip install --no-cache-dir --no-deps .

ENTRYPOINT ["/bin/bash"]
