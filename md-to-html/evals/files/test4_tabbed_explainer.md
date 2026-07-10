# How async/await Works

## TL;DR

async/await is syntactic sugar over Promises. It makes asynchronous code look synchronous, improving readability without changing the underlying event loop model.

## Background

JavaScript is single-threaded. Long-running operations (network requests, file I/O) are handled asynchronously to avoid blocking the main thread. Before async/await, this was done with callbacks and then Promises.

## The three patterns

### Callbacks (pre-ES6)

The original approach. Pass a function to be called when the operation completes.

```js
fs.readFile('data.json', 'utf8', function(err, data) {
  if (err) throw err;
  console.log(JSON.parse(data));
});
```

Problem: deeply nested callbacks become unreadable ("callback hell").

### Promises (ES6)

A Promise represents a value that will be available in the future.

```js
fetch('/api/data')
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));
```

Better than callbacks, but still chains that grow horizontally.

### async/await (ES2017)

Syntactic sugar over Promises. `await` pauses the async function until the Promise resolves.

```js
async function loadData() {
  try {
    const res = await fetch('/api/data');
    const data = await res.json();
    console.log(data);
  } catch (err) {
    console.error(err);
  }
}
```

Same behavior as the Promise chain, but reads top-to-bottom like synchronous code.

## Key rules

- `await` can only be used inside an `async` function.
- An `async` function always returns a Promise, even if you return a plain value.
- Errors from awaited Promises are caught with `try/catch`.
- Multiple independent awaits should use `Promise.all()` to run in parallel.

```js
// Sequential (slow — waits for each)
const a = await fetchA();
const b = await fetchB();

// Parallel (fast — both start at once)
const [a, b] = await Promise.all([fetchA(), fetchB()]);
```

## Common mistakes

- Forgetting `await` — the variable holds a Promise, not the value.
- `await` inside `.forEach()` — forEach does not wait; use `for...of` instead.
- Unhandled rejections — always wrap top-level `await` in try/catch or `.catch()`.

## Compatibility

| Environment | Support |
| --- | --- |
| Node.js | 7.6+ (full), 10+ (stable) |
| Chrome | 55+ |
| Firefox | 52+ |
| Safari | 10.1+ |
| Edge | 15+ |
