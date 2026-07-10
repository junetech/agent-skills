# Feature Flags — Payments v2 Rollout

Current feature flags controlling the payments v2 rollout. All flags default to off in production; on in staging.

## Flags

### payments_v2_enabled

Controls whether the new payments backend is active. Master switch — disabling this disables all other payments_v2_* flags.

- Default: off
- Dependencies: none
- Safe to toggle: yes (falls back to v1 payments)

### payments_v2_new_checkout_ui

Enables the redesigned checkout flow (3-step wizard). Requires payments_v2_enabled.

- Default: off
- Dependencies: payments_v2_enabled
- Safe to toggle: only when payments_v2_enabled is on

### payments_v2_stripe_element

Uses Stripe Elements for card capture instead of the legacy iframe. Requires payments_v2_new_checkout_ui.

- Default: off
- Dependencies: payments_v2_new_checkout_ui, payments_v2_enabled
- Safe to toggle: risky; changes PCI surface — needs security review before enabling in prod

### payments_v2_express_checkout

Shows Apple Pay / Google Pay buttons on checkout. Requires payments_v2_stripe_element.

- Default: off
- Dependencies: payments_v2_stripe_element, payments_v2_new_checkout_ui, payments_v2_enabled
- Safe to toggle: yes (gracefully degraded if browser doesn't support)

### payments_v2_analytics

Sends checkout funnel events to the new analytics pipeline. Independent of other flags.

- Default: off
- Dependencies: none
- Safe to toggle: yes (no user-facing impact)
