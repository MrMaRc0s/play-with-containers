# play-with-containers

This project takes the microservices built for `crud-master` (Inventory API,
Billing API and API Gateway, all written in Python with Flask) and packages
them as a Docker Compose infrastructure instead of the Vagrant VMs used
previously. The goal is the same system, running as six containers on one
Docker host.

## Architecture

```text
Client ──HTTP──> api-gateway-app (:3000)
                    │
                    ├──HTTP──> inventory-app (:8080) ──> inventory-database (:5432)
                    │
                    └──AMQP──> rabbitmq billing_queue ──> billing-app
                                                             │
                                                             └──> billing-database (:5432)
```

Only `api-gateway-app` publishes a port to the host. Every other container is
reachable only from inside the `crud-master-network` bridge network created by
Compose.

| Container | Image | Role |
| --- | --- | --- |
| `inventory-database` | `inventory-database` | PostgreSQL, owns the `movies` table |
| `billing-database` | `billing-database` | PostgreSQL, owns the `orders` table |
| `RabbitMQ` | `rabbitmq` | Message broker, holds `billing_queue` |
| `inventory-app` | `inventory-app` | Flask CRUD API for movies |
| `billing-app` | `billing-app` | Queue consumer that persists orders |
| `api-gateway-app` | `api-gateway-app` | Public entry point, proxies to Inventory and publishes to RabbitMQ |

Docker does not allow uppercase characters in image repository names, so the
RabbitMQ image is built and tagged as `rabbitmq`. The container itself is
still named `RabbitMQ`, which is what shows up in `docker ps`.

## Why containers instead of VMs

A virtual machine virtualizes an entire computer, including its own kernel,
and typically takes tens of seconds to minutes to boot. A container shares the
host kernel and only isolates processes, filesystem and network, so it starts
in a fraction of a second and uses far less memory and disk. Docker is the
tool used here to build images (read-only templates describing a container's
filesystem and startup command) and run them as containers.

This project is a microservices architecture: instead of one monolithic
application, responsibilities are split across independently deployable
services (Inventory, Billing, Gateway) that communicate over the network. This
makes each service independently scalable, deployable and replaceable, at the
cost of needing inter-service communication and coordination.

RabbitMQ is a message queue: a broker that accepts messages from a producer
(the Gateway) and holds them in a durable queue until a consumer (Billing) is
ready to process them. It decouples the two services so that the producer
never blocks or fails just because the consumer happens to be down.

## Prerequisites

- Docker Engine
- Docker Compose (the `docker compose` plugin, or a recent standalone
  `docker-compose`; the extended `depends_on: condition: service_healthy`
  syntax used here needs Compose V2)

## Configuration

Copy the template and adjust it if needed:

```bash
cp .env.example .env
```

`.env` holds every credential and hostname used by the stack and is
git-ignored; only `.env.example` (with placeholder passwords) is committed.
No password or secret is hardcoded anywhere in `docker-compose.yml`,
the Dockerfiles or the application source.

## Build and run

```bash
docker compose up --build
```

Compose builds all six images and starts them in dependency order: the two
databases and RabbitMQ must report healthy before `inventory-app` and
`billing-app` start, and `api-gateway-app` starts once `inventory-app` and
`rabbitmq` are up.

Check everything is running:

```bash
docker ps
docker images
docker volume ls
```

`inventory-database`, `billing-database` and `api-gateway-app` are the three
named volumes; they keep the two databases and the Gateway's log file across
`docker compose down` (without `-v`).

Every service is declared with `restart: on-failure`, so a crashed container
(for example the app inside `billing-app` failing to reach a database before
it's ready) restarts automatically instead of staying down. Verify with:

```bash
docker inspect -f "{{ .HostConfig.RestartPolicy }}" <container-name>
```

Stop everything:

```bash
docker compose down
```

Add `-v` to also delete the named volumes and start from an empty database.

## API endpoints

All client requests go through the Gateway on `http://localhost:3000`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/movies` | Retrieve all movies or filter with `?title=name` |
| `POST` | `/api/movies` | Create a movie |
| `DELETE` | `/api/movies` | Delete all movies |
| `GET` | `/api/movies/:id` | Retrieve one movie |
| `PUT` | `/api/movies/:id` | Update one movie |
| `DELETE` | `/api/movies/:id` | Delete one movie |
| `POST` | `/api/billing` | Place an order on `billing_queue` |

```bash
curl -i -X POST http://localhost:3000/api/movies/ \
  -H 'Content-Type: application/json' \
  -d '{"title":"A new movie","description":"Very short description"}'

curl -i http://localhost:3000/api/movies/

curl -i -X POST http://localhost:3000/api/billing/ \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"20","number_of_items":"99","total_amount":"250"}'
```

A Postman collection is not included in this repository; the requests above
cover every method exposed by the Gateway and can be imported into Postman
individually or wrapped in a collection of your own.

## Inspect the databases

Connecting over the container's Unix socket as anyone other than the
`postgres` OS user hits peer authentication, so go in as `postgres` (its
socket connection is always trusted locally) and pick the database with
`-d`:

```bash
docker exec -it inventory-database runuser -u postgres -- psql -d movies_db -c 'TABLE movies;'
docker exec -it billing-database runuser -u postgres -- psql -d billing_db -c 'TABLE orders;'
```

## Test queue resilience

Send a Billing POST while everything is up, confirm the order lands in
`orders`, then stop only the consumer:

```bash
docker stop billing-app
docker ps
```

Send another Billing POST — the Gateway still returns `200` because RabbitMQ
durably queued the message even though nothing is consuming it yet:

```bash
curl -i -X POST http://localhost:3000/api/billing/ \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"22","number_of_items":"10","total_amount":"50"}'
```

Check `orders` again: the row for `user_id = 22` is not there yet. Restart
the consumer and it will drain the queue:

```bash
docker start billing-app
```

The consumer only acknowledges a message after the matching `INSERT`
succeeds, so restarting it makes the missing order appear in `orders` without
losing anything.

## Design choices

- Every image is built `FROM debian:12-slim` (Bookworm, Debian's previous
  stable release now that Trixie is current) instead of a pre-built
  application or database image — PostgreSQL, RabbitMQ and Python are all
  installed with `apt-get` inside the Dockerfile.
- Each database container's entrypoint starts PostgreSQL once, creates or
  updates its role and database from the environment (idempotent, so
  `docker compose up` again doesn't fail on a second run), stops it, then
  re-execs `postgres` in the foreground so it becomes PID 1 and responds to
  `docker stop`.
- The whole `/var/lib/postgresql` directory is a named volume. Docker
  populates a new named volume from the image's existing content on first
  start, so the cluster created by `apt-get install postgresql` during the
  image build is what ends up on the volume — no separate `initdb` step is
  needed.
- `inventory-app` and `billing-app` never talk to each other directly; the
  Gateway is the only service aware of Inventory's address, and RabbitMQ is
  the only channel between the Gateway and Billing.
- Only `api-gateway-app` has a `ports:` mapping; every other service uses
  `expose:`, which documents the port without publishing it to the host.
- The Gateway writes to both stdout and `/var/log/api-gateway/gateway.log`,
  which is the mounted `api-gateway-app` volume.
