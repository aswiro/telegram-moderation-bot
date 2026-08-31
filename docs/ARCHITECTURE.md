# Architecture

The project uses a layered asynchronous architecture built around aiogram.

```text
Telegram Update
     |
     v
aiogram Dispatcher
     |
     +------------------------------+
     |                              |
     v                              v
Dialogs / Handlers          Middleware Layer
     |                     - Unit of Work
     |                     - Localization
     v
Application Logic
     |
     +-------------+----------------+----------------+
     |             |                |                |
     v             v                v                v
PostgreSQL       Redis          APScheduler     Telegram API
SQLAlchemy       FSM state      background      messages/groups
Repositories                    jobs
```

## Data access

Database access is isolated behind repositories and a Unit of Work. Each update gets its own Unit of Work through middleware. The unit commits on successful completion and rolls back if a handler raises an exception.

## Telegram UI

`aiogram-dialog` is used for stateful administration flows such as group management, manager assignment, announcement management, and language selection.

## Localization

English and Russian resources are stored as Fluent (`.ftl`) files. The preferred language is persisted for registered users and cached in FSM state.

## Background jobs

APScheduler runs periodic announcement delivery. Runtime job state is kept in memory for the showcase version; persistent scheduling can be introduced separately if needed.

## Configuration

All environment-specific values are loaded through Pydantic Settings. Secrets are expected in `.env` locally or environment variables in deployment and must never be committed.

## Deployment

The application supports polling and webhook modes. Docker Compose starts PostgreSQL, Redis, and the bot with health checks for the infrastructure services.

## Public repository scope

This repository contains only sanitized source code and documentation. Production database dumps, logs, Telegram identifiers, invite links, customer data, and historical secrets are intentionally excluded.
