# Plan: Replace in-process cache with shared cache layer

## Context

The `analytics` service caches feature rollups in-process (`functools.lru_cache`). This was fine when we ran one replica; now we run six behind a load balancer and each replica builds the cache independently — a cold-start storm after every deploy.

Two off-the-shelf options. We have prior production experience with both.

- `/infra/redis-cluster/` — already provisioned for the `notifications` service; ops team owns it; supports clustering, persistence, Lua scripts. **Structural template.**
- `/infra/memcached/` — used by the `cms` service; simpler protocol, no persistence, no clustering. **Not** the template — we'd lose write-through and the eviction visibility we already have tooling for.

User decisions (final):

- Cache layer: **Redis** (reuse existing cluster, add a new keyspace prefix).
- Serialization: **msgpack** over JSON — 30% smaller for our rollup shape.
- Cache key shape: `analytics:rollup:{tenant}:{date}:{metric}` — tenant first for namespacing.
- TTL: **24h sliding** with a `lastReadAt` field for LRU tooling.
- **No write-through.** The analytics workers write to Postgres; cache is read-through with a 60s grace period after a write before invalidation.
- In scope: client wrapper, instrumentation (cache_hit / cache_miss / cache_stale metrics), cold-start warmup job. Migration of two endpoints (`/rollup/daily`, `/rollup/weekly`).
- Out of scope (this PR): the third endpoint (`/rollup/realtime`) needs a different access pattern and is tracked separately.

## Goal

Eliminate per-replica cold-start cache rebuild after deploys. Target: P95 `/rollup/daily` latency under 200ms within 60s of a deploy (currently 2-4s for the first 30s).

## File layout

New package under `src/analytics/cache/`:

- `__init__.py` — re-export `CacheClient`, `CacheKey`, `CacheMissError`.
- `client.py` — `CacheClient` (thin wrapper over `redis.Redis` with msgpack codec).
- `keys.py` — `CacheKey` builder + parser. Single source of truth for key shape.
- `warmup.py` — `WarmupJob` — runs on pod startup, populates the top-100 tenant rollups before the readiness probe passes.
- `metrics.py` — Prometheus counters: `cache_hit`, `cache_miss`, `cache_stale`, `cache_warmup_duration_seconds`.

Wiring:

- `src/analytics/handlers/rollup.py` — replace `@lru_cache` decorator with `CacheClient.get_or_compute(...)`.
- `src/analytics/app.py` — register `WarmupJob` in startup hook.
- `infra/k8s/analytics-deployment.yaml` — add `REDIS_URL` env var (from existing secret), bump readiness-probe initialDelay from 5s to 20s to accommodate warmup.

Reuse without copy:

- `redis.Redis` connection from `src/common/redis_pool.py` — do not create a new pool.
- Prometheus registry from `src/common/metrics.py` — register counters there, not in a new file.

## CacheClient API

```python
class CacheClient:
    def get_or_compute(
        self,
        key: CacheKey,
        compute: Callable[[], T],
        ttl_seconds: int = 86400,
        stale_grace_seconds: int = 60,
    ) -> T: ...

    def invalidate(self, key: CacheKey) -> None: ...
    def invalidate_prefix(self, prefix: str) -> int: ...  # returns count
```

`get_or_compute` returns the cached value if present and fresh, else calls `compute()`, stores the result, returns it. On stale entries (within `stale_grace_seconds` of TTL expiry), returns the stale value and triggers an async recompute.

## Risks

1. **msgpack codec deserialization on mixed-version deploys.** If a pod running v2 (msgpack) reads a value written by v1 (JSON), it crashes. *Mitigation:* prefix every value with a 1-byte codec marker (`0x01` = JSON, `0x02` = msgpack); client falls back to JSON for unknown prefixes during a 2-week migration window, then we drop the fallback.

2. **Warmup job lengthens readiness probe.** Bumping `initialDelaySeconds` from 5s to 20s means slower rollout. If warmup itself takes longer than 20s (e.g. Redis is slow), the pod gets killed by the liveness probe before serving traffic. *Mitigation:* cap warmup at 15s wall-clock; if it doesn't finish, log a WARN and proceed — first requests will be slow but the pod stays up.

3. **Stale grace breaks read-your-write for the rollup endpoints.** A user who triggers a rollup recompute via the admin UI then reloads the page might see the old value for up to 60s. *Mitigation:* admin UI sends `Cache-Control: no-cache` header; client honors it and bypasses cache for that request.

4. **Redis cluster failure.** If the cluster goes down, `/rollup/*` endpoints currently degrade to direct DB queries via the in-process cache. With the new wrapper, they'd hard-fail. *Mitigation:* `CacheClient.get_or_compute` catches `redis.ConnectionError` and falls back to calling `compute()` directly (with a metric increment so we can alert).

5. **Memory pressure on the shared cluster.** The `notifications` service already uses ~40% of the cluster. Adding rollup data (estimated 200MB at p99) pushes us toward eviction territory. *Mitigation:* before merging, run `redis-cli --memkeys` against the staging cluster with both workloads; if we project >75% usage, request a cluster upsize first.

## Deferred (explicitly)

- **Realtime rollup endpoint** — needs sub-second invalidation; cache shape would be different.
- **Per-tenant cache quotas** — would need Redis Cluster slot accounting; defer until we see a single tenant blow up memory.
- **Pre-aggregation in Postgres materialized views** — orthogonal optimization; can compose with this cache.
