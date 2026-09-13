FROM debian:12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends rabbitmq-server \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 5672
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
