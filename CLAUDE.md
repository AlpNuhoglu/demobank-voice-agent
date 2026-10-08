# CLAUDE.md

## Project

A Turkish-language voice agent for a fictional bank ("Demo Bank"), built on
ElevenLabs Agents. This repo is the backend the agent calls through server
tools and webhooks.

## Rules

- All data is synthetic. Never use real bank names, real people, or real card
  or phone numbers.
- Secrets live only in `.env` (gitignored). Commit `.env.example` with
  placeholders. Tests must pass without any real API key.
- Show a plan before writing code, work in small steps, and run `pytest` and
  `ruff` before every commit.
- Never log phone numbers, SMS codes, card digits beyond the last four, or
  hashes of any of them.
- Stack: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 with SQLite, uv,
  pytest, ruff.
- When behaviour depends on ElevenLabs, check the current ElevenLabs
  documentation instead of assuming.
- Parts of this repo are developed in cloud sessions without inbound network
  access: tests must never require a tunnel or a live ElevenLabs call.
