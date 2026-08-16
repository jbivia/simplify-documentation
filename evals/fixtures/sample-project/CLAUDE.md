# CLAUDE.md

This document describes the TaskRunner project and provides guidance for AI
assistants working in this repository. Please read it carefully before making
any changes to the codebase.

## About the project

TaskRunner is a small job queue with an HTTP API. It was originally built in
2023 as an internal tool and has since been extracted into its own repository.
The project is written in JavaScript and runs on Node.js.

## Project Structure

The repository follows a standard Node.js layout:

```
taskrunner/
├── src/
│   ├── api/          - HTTP layer, Express routes and middleware
│   │   ├── server.js - Entry point, starts the Express app
│   │   └── routes.js - Route definitions
│   ├── models/       - Sequelize models for the database
│   ├── services/     - Business logic
│   │   └── jobs.js   - Job creation and state transitions
│   ├── queue/        - Queue abstraction
│   ├── workers/      - Background workers
│   ├── legacy/       - Old v1 code, being migrated, do not add to it
│   └── utils/        - Shared helpers
├── tests/            - Test files
├── package.json      - Dependencies and scripts
└── README.md         - User-facing documentation
```

## Dependencies

The project uses the following main dependencies:

- express - the web framework used for the HTTP API
- sequelize - ORM used for database access
- better-sqlite3 - the underlying SQLite driver
- eslint - linting
- prettier - code formatting

Please do not add new dependencies without discussing it first.

## Commands

- `npm install` - install dependencies
- `npm start` - start the server
- `npm run dev` - start the server in watch mode
- `npm test` - run the test suite
- `npm run lint` - run the linter
- `npm run migrate` - apply database migrations

## Code Style

Please follow these code style rules when writing code in this repository:

- Use 2 spaces for indentation, never tabs
- Always use single quotes for strings
- Add semicolons at the end of every statement
- Maximum line length is 100 characters
- Use camelCase for variables and functions, PascalCase for classes
- Prefer const over let, and never use var
- Use async/await rather than raw promise chains

## Testing

We use the built-in Node.js test runner. Tests live in the `tests/` directory
and are named after the module they test. It is very important that you write
tests for any new functionality that you add to the codebase, and that you run
the full test suite before committing your changes. Tests must be run serially
because they share the same SQLite file — running them in parallel causes
intermittent failures that are very hard to debug.

## Example: adding a new task handler

Here is an example of how to add a new task handler to the project:

```javascript
// src/workers/handlers.js
async function myNewHandler(payload) {
  // Validate the payload first
  if (!payload.something) {
    throw new Error('something is required');
  }

  // Do the actual work here
  const result = await doTheWork(payload.something);

  // Return the result, it will be stored in the jobs table
  return result;
}

module.exports = { echo, sum, myNewHandler };
```

Once you have added the handler, it will automatically be picked up by the
worker when a job with a matching task name is created.

## Important notes

- The API returns 200 or 202 for known routes even when the underlying job
  fails. Failures are reported in the job's `status` field, so never rely on
  the HTTP status code to determine whether a job succeeded.
- Never flush the Redis cache manually in production — the ops team relies on
  it staying warm during the nightly batch window.
- The `src/legacy/` folder is deprecated. Do not add new code there.

## General guidance

- Write clean, readable, well-documented code
- Follow existing patterns in the codebase
- Handle errors properly and never swallow exceptions
- Keep functions small and focused on a single responsibility
- Add comments explaining complex logic
- Make sure your changes do not break existing functionality

## History

- v1.0 (2023) - initial internal release, used a Redis-backed queue
- v2.0 (2024) - migrated to SQLite, dropped the Redis dependency
- v2.1 (2024) - added the retry mechanism

Thanks for reading, and feel free to update this file as the project evolves!
