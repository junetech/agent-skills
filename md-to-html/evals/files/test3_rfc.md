# RFC: Error reporting policy for the SDK

## Background

We ship a client SDK in seven languages. Each language's error model is different — exceptions in Python and Ruby, error returns in Go, `Result` in Rust, rejected promises in TypeScript and Swift, exceptions again in Java. Today every SDK author has made their own choice about what to surface from the network layer and what to swallow, what to wrap in our own error type and what to pass through, and whether to include the underlying transport error as a cause.

This inconsistency creates two problems. First, users who write polyglot integrations (a common pattern — backend in Go, frontend in TypeScript, mobile in Swift) get a different error vocabulary in each language and have to translate between them mentally. Second, our support team can't write a single playbook for diagnosing common issues; every "did you check for `NetworkError`?" instruction has to be language-qualified, and the SDK changelog has to call out error-type changes per language even when the underlying behavior is identical.

This RFC proposes a single policy that all SDKs follow, with language-idiomatic surfaces. The intent is not to make every SDK look like Go's `error` interface — it's to make the *content* and *categories* of errors identical even when the *shape* differs by language.

## Principles

The policy rests on three principles that we should apply when designing each language's surface.

First, **the error category is part of the public API, the message is not.** A user catching `NetworkError` is writing supported code; a user grepping the message string is writing fragile code we won't promise to support. We document categories; we don't document message contents.

Second, **the underlying transport error must always be reachable.** Wrapping is fine and language-idiomatic, but the user should be able to get at the original `urllib3.HTTPError` or `net.OpError` if they need to. We don't strip context for the sake of a clean API.

Third, **we don't invent errors that don't correspond to a wire condition.** If the server returned a 200 with a malformed body, that's one category (parsing). If the network failed before any byte came back, that's a different category (network). We don't collapse them into a single "request failed" because the operational response is different — one is a server bug, the other is a connectivity issue.

## Category choice

The two candidate taxonomies were Stripe's (which uses ~12 error classes including things like `IdempotencyError`, `RateLimitError`, `APIConnectionError`) and Google Cloud's (which uses ~16 status codes mirroring gRPC). Both are well-thought-out and battle-tested.

We adopt **a reduced Stripe-style taxonomy** (5 categories): `NetworkError`, `ParseError`, `AuthError`, `ClientError` (4xx other than 401/403), `ServerError` (5xx). The reasoning: our SDK surface is narrower than Stripe's, our users skew toward backend integration rather than mobile-first, and Google's gRPC-aligned taxonomy is too granular for use cases that mostly don't care about the difference between `DEADLINE_EXCEEDED` and `UNAVAILABLE` — they just want to retry.

## Decisions

- **Categories: 5** (NetworkError, ParseError, AuthError, ClientError, ServerError). Frozen.
- **Inheritance: single root** (`SDKError` in languages that support it; an interface in Go; a trait in Rust). All categories inherit/implement the root.
- **Retry semantics on the category**: `NetworkError` and `ServerError` are retryable; the rest are not. The SDK exposes `error.is_retryable()` so users don't have to switch on category.
- **Underlying transport error**: always exposed as `error.cause()` (or the language equivalent).
- **Status code**: exposed on `ClientError` and `ServerError` as `error.status_code()`; absent on the others.

## Implementation phasing

Each SDK ships the new taxonomy in its next major version. Old error types are deprecated but still raised in parallel for one minor-version cycle (so a user catching the old type continues to work), then removed. Migration guide per language goes in the SDK docs site.

This is not a coordinated single release across all seven SDKs — each language ships when it ships. We accept the cross-language inconsistency window of ~3 months as the cost of not blocking SDK releases on each other.

## Out of scope for this RFC

- Telemetry on which error categories fire in production (separate observability project).
- Server-side error message standardization (the wire format is what it is; this RFC is purely about how SDKs present it).
- Localization of error messages (English only for now; not promised as an API).
