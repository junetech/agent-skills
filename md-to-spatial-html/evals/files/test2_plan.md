# Plan: Migrate auth from server sessions to JWT

## Context

Current auth uses server-side sessions stored in Postgres (`sessions` table, lookup per request). At our current 8k RPS this is ~20% of DB load. Two paths forward:

- **Redis-backed sessions.** Lower latency than Postgres lookup, but keeps the server-side state model and ops burden.
- **JWT with short-lived access tokens + refresh tokens.** Stateless verification on the request path, only DB lookup on refresh.

User decisions (final):

- **JWT with refresh tokens** (the stateless path). Access tokens: 15min lifetime. Refresh tokens: 30d lifetime, opaque, stored in Postgres.
- Signing: **RS256** (rotate keys quarterly; JWKs endpoint at `/.well-known/jwks.json`).
- Claims: `sub` (user_id), `tenant`, `roles` (array), `iat`, `exp`. Nothing more — keep tokens small.
- **No revocation list for access tokens.** 15min lifetime is short enough that we accept the window.
- Refresh tokens **are revocable** (DB-backed, single row, rotated on every refresh).

Companion document: `test2_detail.md` — covers key rotation mechanics, the rollout phasing, and the security review notes.

## In scope

- `src/auth/jwt.py` — sign/verify with current and previous keys (during rotation window).
- `src/auth/refresh.py` — refresh token store, rotation, revocation.
- `src/middleware/authz.py` — replace session lookup with JWT verification.
- `/auth/login`, `/auth/refresh`, `/auth/logout` endpoints.
- Migration: existing session cookies are honored until they expire (max 7d); new logins issue JWT.

## Risks

1. **Clock skew across services.** A request signed at t=0 verified at t=-30s on a downstream service fails on `iat > now`. *Mitigation:* allow 60s clock skew in verification (`leeway=60`).

2. **JWKs endpoint becomes a hot dependency.** Every service verifying tokens fetches keys from there. *Mitigation:* cache JWKs in-process for 1h; on `kid` miss, refetch once before failing.

3. **Refresh token theft.** If an attacker steals a refresh token, they get 30d access. *Mitigation:* rotate refresh token on every use; if a rotated refresh token is presented twice, revoke the whole chain and force re-auth (theft signal).

## Verification

- Unit tests for sign/verify with active + previous key.
- Integration test: full login → request → refresh → request → logout flow.
- Load test: 10k RPS with JWT verification; assert P99 < 5ms on the verification path.
- Manual: rotate keys in staging, watch metrics for failed verifications during the rollover window.

## Deferred

- mTLS for service-to-service auth (different problem, different doc).
- Device-bound tokens (would need a token binding extension; revisit if we see refresh-token theft incidents).
