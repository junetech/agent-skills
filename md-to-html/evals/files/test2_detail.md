# JWT Migration — Detail Decisions

Companion to `test2_plan.md`. Overrides any conflicting wording there.

## Key rotation mechanics

We keep **two** RSA keypairs live at any time: `current` and `previous`. The JWKs endpoint exposes both. Verification accepts tokens signed by either; signing always uses `current`.

Rotation procedure (quarterly):

1. Generate a new keypair offline.
2. Deploy the public key as the new `current` in the JWKs config; demote the existing `current` to `previous`; drop the old `previous`.
3. Wait 15min (max access-token lifetime) so all in-flight tokens signed by the old `previous` have expired.
4. Update signing service to use the new `current` private key.

The 15min wait is the load-bearing reason access tokens are 15min, not 1h.

## Rollout phasing

| Phase | Duration | Behavior |
| --- | --- | --- |
| 0 | 1 week | Both session cookies and JWT supported. New logins issue JWT only. |
| 1 | 6 weeks | Session cookies still honored (legacy users who haven't logged in). |
| 2 | — | Session middleware removed. Any remaining session cookies result in re-auth prompt. |

The 7-week gap is governed by the longest session lifetime (30d) plus a 4-week buffer for inactive users.

## Security review notes (from internal pen-test 2026-04)

- **RS256 over HS256.** Approved. HS256 would require shared secret distribution; RS256 lets verifiers hold only the public key.
- **No `nbf` claim.** Approved. We don't have a use case that needs delayed validity.
- **Refresh token format: opaque random 32 bytes, base64url.** Approved over UUID v4 (smaller entropy footprint).
- **Token storage on the client: httpOnly secure cookie for refresh, in-memory for access.** Approved. Rejects localStorage for refresh tokens.

## Out of scope

- OAuth2 / OIDC compatibility (we don't federate currently).
- Token binding (defer until we see theft incidents).
- Per-token audience claims (single audience for now: the `api` service).
