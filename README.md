# Telegram Group Management & Automation Bot

<p align="center">
  <img src="docs/assets/telegram-moderation-bot-cover.jpg" alt="Telegram Group Management & Automation Bot" width="900" />
</p>

A production-oriented Telegram group management bot built with Python and aiogram 3.

This repository is a **sanitized public showcase** of a larger private project. Production credentials, database dumps, runtime logs, real Telegram IDs, invite links, and other operational data are intentionally excluded.

## What it demonstrates

- Telegram bot development with **aiogram 3** and **aiogram-dialog**
- Group registration and management from an admin dialog
- Manager assignment from Telegram group administrators
- Advertisement/content management and scheduled delivery
- PostgreSQL persistence with async **SQLAlchemy 2**
- Repository + Unit of Work data-access pattern
- Redis-backed FSM storage
- English/Russian localization with Fluent
- Polling and webhook deployment modes
- Docker / Docker Compose deployment
- Alembic-ready database migrations
- Structured application logging
- Environment-based configuration with Pydantic Settings

## Architecture

```text
Telegram
   |
   v
aiogram Dispatcher
   |
   +-- Dialogs / Handlers
   +-- Localization Middleware
   +-- Unit of Work Middleware
   |
   v
Application Services
   |
   +-- PostgreSQL / SQLAlchemy
   +-- Redis FSM Storage
   +-- APScheduler
```

More details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## Tech stack

Python 3.12 · aiogram 3 · aiogram-dialog · SQLAlchemy 2 · PostgreSQL · Redis · Alembic · APScheduler · Fluent · Pydantic Settings · Docker

## Quick start

### 1. Clone the repository

```bash
git clone git@github.com:aswiro/telegram-moderation-bot.git
cd telegram-moderation-bot
```

### 2. Create the environment file

```bash
cp .env.example .env
```

Fill in your own Telegram bot token, super-admin ID, and local database settings.

### 3. Run with Docker Compose

```bash
docker compose up --build
```

Or install locally with [`uv`](https://docs.astral.sh/uv/):

```bash
uv sync
uv run python main.py
```

## Configuration

All runtime settings are provided through environment variables. See [`.env.example`](.env.example).

**Never commit `.env`, database dumps, logs, real Telegram IDs, tokens, passwords, or production exports.**

## Public showcase note

The original private repository contained operational artifacts and historical development data that are not appropriate for a public portfolio. This repository was created with a fresh Git history and contains only sanitized source code and documentation.

## Security

If you discover a security issue, please see [`SECURITY.md`](SECURITY.md). Do not publish credentials or sensitive operational data in an issue.

## License

This repository is provided as a portfolio showcase. No open-source license is granted unless a license file is added explicitly.
