# TaskRunner

## Introduction

Welcome to TaskRunner! TaskRunner is a lightweight, easy-to-use job queue
solution that comes with a built-in HTTP API. It was designed from the ground
up to be simple to operate, with minimal external dependencies, so that small
teams can get asynchronous background processing up and running without having
to deploy and maintain a complex piece of infrastructure.

It is important to note that TaskRunner is not intended to be a replacement for
a fully featured distributed task queue. If your workload requires distributed
execution across multiple machines, you will probably want to look at other
solutions instead.

## Requirements

Before you get started, please make sure that you have the following installed
on your machine:

- Node.js version 16 or higher
- npm (which is bundled with Node.js)
- A Redis server (optional, only needed if you enable the caching layer)

## Installation

In order to install TaskRunner, you should first clone the repository to your
local machine. Once that has been done, you can then install the dependencies
by running the following command:

```
npm install --production
```

After the dependencies have been installed, the next thing that you will need
to do is to start the server. This can be accomplished by running:

```
npm start
```

By default, the server will start up and begin listening for incoming HTTP
requests on port 8080. The background worker is started automatically as part
of the server process, so there is nothing else that you need to do.

## Configuration

TaskRunner can be configured by means of environment variables. The following
environment variables are supported by the application:

- `PORT` - the port that the HTTP server listens on
- `DATABASE_URL` - the path to the SQLite database file
- `REDIS_URL` - the connection string for the Redis cache
- `LOG_LEVEL` - how much logging output should be produced

## Architecture

The architecture of the application is modular in nature. When a request comes
in over HTTP, it is first handled by the API layer, whose responsibility it is
to validate the incoming request and to make sure that it is well formed. After
validation has been performed, the request is then passed along to the service
layer. The service layer is where the business logic of the application lives,
and it is here that a job record is created and persisted to the database. Once
the job record has been created, the identifier of that job is placed onto the
queue, from where it will subsequently be picked up by one of the background
workers. The background worker will then look up the appropriate handler for
the task in question and will execute it. In the event that the handler throws
an error, the job will be marked as failed, and it will then be retried, up to
a maximum number of attempts, after which point it will be marked as
permanently failed and will not be retried any further.

## Usage

To create a job, send a POST request to the `/jobs` endpoint:

```
curl -X POST http://localhost:8080/jobs \
  -d '{"task": "sum", "payload": {"numbers": [1, 2, 3]}}'
```

To check on the status of a job, send a GET request to `/jobs/:id`.

## Testing

Tests can be run with `npm test`. Please note that the test suite requires the
database to have been migrated first.

## License

MIT
