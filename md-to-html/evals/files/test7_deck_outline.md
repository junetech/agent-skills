# Incident Post-mortem: Payments Outage 2026-06-20

Presentation for the all-hands engineering review. 5 slides.

## Slide 1: What happened

On 2026-06-20 at 14:32 UTC, the payments service became unavailable for 23 minutes.
All checkout attempts returned HTTP 503. Approximately 1,400 transactions failed.

Impact: ~$47,000 in lost GMV; no data loss; no security incident.

## Slide 2: Timeline

- 14:32 UTC — First 503s reported by uptime monitor.
- 14:35 UTC — PagerDuty alert fired; on-call engineer acknowledged.
- 14:41 UTC — Root cause identified: Redis connection pool exhausted.
- 14:48 UTC — Rollback of deploy #3917 initiated.
- 14:55 UTC — Service restored; error rate back to baseline.

## Slide 3: Root cause

Deploy #3917 introduced a new background job that opened a Redis connection per task without releasing it. Under load, the connection pool (max 50) was exhausted within 8 minutes of deploy.

The background job was not load-tested against a pool-constrained environment. Staging uses an uncapped mock Redis.

## Slide 4: Contributing factors

- No connection-pool exhaustion alert existed.
- Staging Redis is uncapped; production pool limit (50) was not documented.
- Deploy rollback procedure required manual steps; no automated rollback on error-rate spike.

## Slide 5: Action items

1. Add Redis connection pool utilization alert (threshold: >80%). Owner: infra team. Due: 2026-06-27.
2. Cap staging Redis pool to match production. Owner: infra team. Due: 2026-06-27.
3. Instrument background jobs to track connection acquisition time. Owner: payments team. Due: 2026-07-04.
4. Automate rollback on P95 error rate >5% for 2 minutes post-deploy. Owner: platform team. Due: 2026-07-11.
