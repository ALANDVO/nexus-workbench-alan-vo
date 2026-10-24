# Changelog

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-15

### Added
- FastAPI backend with async SQLAlchemy and SQLite persistence
- React 18 + TypeScript + Vite frontend with typed API client
- OIDC Authorization Code flow with PKCE via Keycloak
- Role-based access control (viewer, operator, admin)
- Analysis CRUD API with pagination, filtering, and status tracking
- Docker Compose with backend, frontend, Keycloak, and persistent volumes
- CI/CD pipeline with backend (pytest) and frontend (vitest, tsc, build) tests
- Health check endpoints for all services
- Comprehensive test suite: 19 backend tests, 8 frontend tests
- Portfolio metadata and documentation

### Architecture
- Domain-driven structure with separate API, core, models, services layers
- Deterministic analysis engine foundation for vtable, switch, JMP+call, string recovery
- LLM provider abstraction (OpenAI-compatible, Anthropic, Gemini, Ollama)
- Keycloak realm with SAML broker support documented

## [Unreleased]

### Planned
- Decompiler output parsing and AST construction
- VTable resolution (Ghidra #516)
- Switch statement recovery (Ghidra #2628)
- JMP+PUSH call recovery (Ghidra #5747)
- Cross-segment string recovery (Ghidra #4865)
- Scalable batch decompilation (Ghidra #2791)