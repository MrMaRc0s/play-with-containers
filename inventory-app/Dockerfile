FROM debian:12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app

COPY requirements.txt .
RUN python3 -m venv .venv \
    && ./.venv/bin/pip install --disable-pip-version-check --no-cache-dir --requirement requirements.txt

COPY . .

EXPOSE 8080
CMD ["/opt/app/.venv/bin/python", "server.py"]
