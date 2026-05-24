# Cache Strategy

This document describes the HTTP caching behaviour of the `aether-knowledge`
origin and the corresponding subscriber-side strategy in `ckl aether sync`.

## Current setup (v0.4 dogfooding)

The repo is served via **GitHub Pages**, which:

- Cannot honour a `_headers` file or `Cache-Control: immutable`.
- Sends every response with a fixed `Cache-Control: max-age=600` (10 min) and a
  strong `ETag`.

Subscriber behaviour:

- `ckl aether sync` uses conditional GET (`If-None-Match: <etag>`) via `ureq`,
  so unchanged files return `304 Not Modified` after the initial fetch. Body
  transfer is skipped on revalidation.
- The 10-minute TTL only affects the time window in which a subscriber might
  read a stale `manifest.json` / `chain.json` index. Slice CBOR files and
  `slice_root.bin` files are content-addressed by hash inside the manifest, so
  a stale index simply postpones discovery of new slices by ≤10 minutes.
- Bandwidth amplification on busy peaks is bounded by the 304 response size
  (~200 bytes/request), which is acceptable for the dogfooding scale of a
  single publisher and ≤100 subscribers.

**Decision (E5-D.2.a, Option A):** Accept the GH Pages defaults for v0.4.
Document the constraint and rely on subscriber-side conditional GETs.

## Future migration (Area F)

When publication volume or subscriber count grows, migrate the origin to
**Cloudflare Pages** (or equivalent). The migration unlocks:

- `_headers` support, so we can mark CAS blobs and CBOR slice files with
  `Cache-Control: public, max-age=31536000, immutable` (one-year cache, never
  revalidate). They are content-addressed, so the bytes for a given URL are
  guaranteed not to change.
- A separate, shorter cache window for the mutable index files
  (`manifest.json`, `chain.json`) — e.g. `max-age=60, s-maxage=300`.
- Edge POPs in regions GitHub Pages does not serve well.

The migration is mechanical (push the same static tree to a different origin,
update DNS for `aether.koslab.ai`). It is intentionally deferred until
post-dogfooding so we get real subscriber-load numbers first.

## Subscriber-side guidance

Subscribers who want lower-latency reads should:

- Use `ckl aether sync --interval 60s` (or shorter) to reduce the worst-case
  staleness window for new slices.
- Keep the local slice cache warm; the digest check in `verify_package`
  guarantees that even a stale-but-valid slice is safe to consume.
