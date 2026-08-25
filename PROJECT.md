# PROJECT.md

# Kotak Neo Live Market Server Pro

Version: Draft 0.1 Date: 2026-07-29

> This document is intended to become the single source of truth for the
> project. It is based on all currently available discussion context. It
> should be updated as development progresses.

------------------------------------------------------------------------

# 1. Project Vision

Build a production-grade Kotak Neo Live Market Server that provides a
reusable backend for trading tools, dashboards, scanners, bots, and
analytics.

Primary goals:

-   Automatic login
-   Automatic TOTP generation
-   Session management
-   Live market data
-   Instrument database
-   Symbol search
-   Dynamic subscriptions
-   REST APIs
-   WebSocket streaming
-   Robust logging
-   Modular architecture

------------------------------------------------------------------------

# 2. Why this project exists

The official SDK alone is not sufficient as the project's foundation
because we encountered authentication inconsistencies while testing. The
objective is to implement the authentication flow according to the
official REST documentation and build the remaining modules around that.

------------------------------------------------------------------------

# 3. Work Completed So Far

## Initial architecture discussed

-   config.py
-   auth.py
-   websocket.py
-   database.py
-   search.py
-   download_master.py
-   server.py

## Existing bridge

An earlier monolithic bridge existed that: - Logged in - Connected
websocket - Streamed live prices - Used manual TOTP

## Investigation performed

Verified: - Mobile number - UCC - MPIN - TOTP generation - Latest SDK
version - SDK login flow

Observed errors: - Invalid field 'MobileNumber' - Missing Auth - Missing
Sid - 2FA incomplete errors

Conclusion: SDK authentication does not appear to align with the
documented login flow.

------------------------------------------------------------------------

# 4. Documentation Findings

Authentication is a two-step REST process.

Step 1: POST tradeApiLogin

Returns: - View Token - View SID

Step 2: POST tradeApiValidate

Returns: - Trade Token - Trade SID - Base URL - Data Center

These values become the authenticated session.

REST documentation will be treated as the authoritative reference.

------------------------------------------------------------------------

# 5. Final Planned Architecture

Kotak-Neo-Live-Server-Pro/

data/ cache/ logs/

Modules

-   config.py
-   logger.py
-   session.py
-   auth.py
-   database.py
-   scripmaster.py
-   websocket.py
-   search.py
-   subscribe.py
-   server.py

------------------------------------------------------------------------

# 6. Authentication Design

Flow:

Generate TOTP

↓

tradeApiLogin

↓

Store View Token + View SID

↓

tradeApiValidate

↓

Store Trade Token + Trade SID

↓

Initialize session

↓

Connect websocket

↓

Serve APIs

Features: - Automatic login - Automatic refresh - Automatic re-login
after expiry

------------------------------------------------------------------------

# 7. Planned Modules

config.py - Environment loading

logger.py - Logging

session.py - Runtime session storage

auth.py - REST authentication

database.py - SQLite

scripmaster.py - Instrument master download

search.py - Symbol lookup

websocket.py - Live feed

subscribe.py - Dynamic subscription manager

server.py - FastAPI endpoints

------------------------------------------------------------------------

# 8. Features

Current planned capabilities:

✓ Automatic TOTP

✓ REST authentication

✓ Session renewal

✓ SQLite instrument database

✓ Daily master download

✓ Fast search

✓ Live websocket

✓ Dynamic subscriptions

✓ REST APIs

✓ Production logging

✓ Error handling

------------------------------------------------------------------------

# 9. Development Roadmap

Phase 1 - Project setup

Phase 2 - Authentication

Phase 3 - Session manager

Phase 4 - Database

Phase 5 - Instrument download

Phase 6 - Search engine

Phase 7 - WebSocket

Phase 8 - REST server

Phase 9 - Testing

Phase 10 - Production deployment

------------------------------------------------------------------------

# 10. Known Issues

-   SDK authentication behaviour differs from documented flow.
-   Authentication implementation remains to be completed and validated.
-   WebSocket integration will begin after successful REST
    authentication.

------------------------------------------------------------------------

# 11. Pending Work

-   Implement auth.py
-   Validate REST login
-   Store session tokens
-   Download instrument master
-   Implement search
-   Implement websocket
-   Build REST server
-   Add health endpoint
-   Add monitoring
-   Add reconnection logic

------------------------------------------------------------------------

# 12. Coding Standards

-   Modular design
-   Type hints where practical
-   Clear logging
-   Minimal global state
-   Production-ready error handling

------------------------------------------------------------------------

# 13. Future Enhancements

-   Order APIs
-   Portfolio APIs
-   Holdings
-   Positions
-   Historical candles
-   Multi-user support
-   Redis caching
-   Docker deployment
-   Prometheus metrics
-   CI/CD pipeline

------------------------------------------------------------------------

# 14. Change Log

## 2026-07-29

-   Project architecture finalized.
-   Authentication redesigned to use REST documentation.
-   Module layout finalized.
-   Initial implementation order defined.

------------------------------------------------------------------------

# 15. Notes

This file is intended to evolve throughout the project. Every
architectural decision, implementation detail, debugging finding, and
milestone should be added here so it becomes the permanent project
reference.
