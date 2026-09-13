FROM debian:12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql \
    && rm -rf /var/lib/apt/lists/*

RUN echo "listen_addresses = '*'" >> /etc/postgresql/15/main/postgresql.conf \
    && echo "host all all 0.0.0.0/0 md5" >> /etc/postgresql/15/main/pg_hba.conf

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 5432
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
