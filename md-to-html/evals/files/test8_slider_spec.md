# CSS Animation Parameter Spec

Spec for the hero section entry animation. Parameters to expose in the sandbox for design review.

## Parameters

### duration

How long the animation takes from start to finish.

- Range: 100ms – 2000ms
- Default: 400ms
- Step: 50ms
- Notes: Values above 800ms feel slow for entry animations; below 150ms may be imperceptible.

### easing

The timing function controlling acceleration.

- Options: ease, ease-in, ease-out, ease-in-out, linear
- Default: ease-out
- Notes: ease-out (fast start, slow finish) is conventional for elements entering the viewport.

### translate-y

Vertical offset the element starts from (slides up to 0 on entry).

- Range: 0px – 80px
- Default: 24px
- Step: 4px
- Notes: Large values (>60px) feel heavy; 16–32px is the sweet spot for subtle entry.

### opacity-start

Initial opacity before the animation begins.

- Range: 0 – 1 (step 0.05)
- Default: 0
- Notes: Starting at 0 (fully transparent) and fading to 1 is the standard fade-in. Starting at 0.5 gives a softer entry.

### scale-start

Initial scale before the animation begins.

- Range: 0.8 – 1.0 (step 0.01)
- Default: 0.96
- Notes: Scale + fade is the modern card-entry pattern. Values below 0.9 look like a pop-in, which is usually too dramatic.

## Deliverable

After tuning, copy the final parameter values and paste them into the design token file at `src/styles/tokens/animation.css`.
