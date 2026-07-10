# Sprint 42 Triage — Open Tickets

Tickets from the backlog that need triage before sprint planning on 2026-06-30.

## Backlog

- **AUTH-201**: Login page flickers on iOS Safari during form autofill. Priority: high. Reporter: mobile QA. No workaround.
- **AUTH-202**: Session expiry warning shows 10s too early on slow connections. Priority: medium. Latency-dependent bug.
- **PERF-118**: Dashboard loads 3.2s on first paint; target is <1s. Priority: high. Profiled: render-blocking font load.
- **PERF-119**: Search endpoint returns full documents when only IDs needed. Priority: medium. Adds ~400ms per query.
- **UI-334**: Date picker does not support keyboard navigation. Priority: medium. Accessibility regression.
- **UI-335**: Dark mode switch resets on page refresh. Priority: low. LocalStorage key conflict.
- **INFRA-077**: Staging deploys fail intermittently when two PRs merge within 30s. Priority: high. Race condition in deploy script.
- **INFRA-078**: Log retention policy not enforced; logs older than 90d still present. Priority: low. Storage cost concern.

## Done (already resolved this week)

- **AUTH-199**: Fix OAuth callback URL mismatch on production. Resolved in #2841.
- **PERF-115**: Add HTTP/2 push for critical CSS. Resolved in #2839.
