# Aether Knowledge — KOSLAB Publisher

L3 knowledge layer publications by **KOSLAB**, served as a static
HTTP origin for the [Aether v0.4](https://github.com/Koslab-DevOrg/ckl)
T1 Bulk Transport protocol (CKL).

- **Origin:** <https://aether.koslab.ai>
- **Publisher manifest:** [/publishers/koslab/](./publishers/koslab/)
- **Protocol:** Aether v0.4 (CKL)

## What this is

This repository is the source-of-truth for KOSLAB's published knowledge
slices. Every commit on `main` is mirrored to GitHub Pages at
`aether.koslab.ai`, where any CKL subscriber can fetch it. Slices are
cryptographically signed: subscribers verify the publisher certificate
chain, the manifest signature, and per-slice digests before consuming
any data.

## Subscribing

From any CKL workspace with `ckl` ≥ `v0.5.32` installed:

```sh
ckl aether subscribe https://aether.koslab.ai/publishers/koslab/
```

This adds KOSLAB as a trusted publisher and starts an `aether sync`
loop that pulls new slices on a configurable interval. The first sync
fetches the full manifest + chain; subsequent syncs use conditional
GETs (see [`docs/cache-strategy.md`](./docs/cache-strategy.md)).

### Prerequisites

- `ckl` binary `v0.5.32` or later (see
  [releases](https://github.com/Koslab-DevOrg/ckl/releases)).
- Network access to `aether.koslab.ai`.
- A local workspace initialised with `ckl init`.

## Layout structure

```
publishers/
  koslab/
    pkg/
      manifest.json          ← root manifest (signed)
      publisher_cert.cbor    ← KOSLAB publisher certificate
      entities/
        <entity_id>/
          chain.json         ← signed slice chain for this entity
          slices/<sid>.cbor  ← per-slice signed CBOR records
          slice_roots/<sid>.bin  ← raw slice-root bytes (digest cross-check)
      blobs/                 ← reserved for CAS payloads (empty in v0.4)
```

- `manifest.json` is the only authoritative entrypoint. Subscribers
  fetch it first, verify the publisher cert + signature, then walk the
  entity list.
- `chain.json` carries the head pointer and per-slice digests for one
  entity. Verified against the publisher cert.
- Slice CBOR files contain a `SignedPackage` (the actual block payload)
  plus a `SliceManifest` (slice-root metadata).
- `blobs/` is reserved-empty in v0.4 per spec D-§4.4-1; CAS storage
  lands in a later protocol version.

For the full protocol spec, see the CKL repo
([`crates/ckl-aether-format`](https://github.com/Koslab-DevOrg/ckl/tree/main/crates/ckl-aether-format)).

## Verification

To validate a publication offline (or before deploying a new one):

```sh
ckl verify-publication ./publishers/koslab
# or, for CI-grade checks:
ckl verify-publication ./publishers/koslab --strict --json
```

Exit codes:

- `0` — layout is valid (signatures + digests + cross-checks all pass).
- `1` — verification failed (signature mismatch, tampered slice, missing file, ...).
- `2` — warnings present and `--strict` flag set (e.g. zero TTL, oversize layout).
- `3` — invocation / IO error (path missing, permissions, ...).

The CI workflow in `.github/workflows/publish.yml` runs this in
`--strict --json` mode on every push and dispatch.

## Tag scheme

Publications are versioned with **semver tags** of the form:

```
pub-vMAJOR.MINOR.PATCH
```

- `MAJOR` bumps on incompatible protocol changes (e.g. v0.4 → v0.5).
- `MINOR` bumps on additive content (new entities, new published slices).
- `PATCH` bumps on metadata-only changes that don't alter slice bytes.

Every `pub-v*` tag is:

1. Signed by the operator (`git tag -s`).
2. Protected at the repo level — only admins can create/push them.
3. Triggers the `publish.yml` workflow → `validate` → `deploy` → GH Pages.

## Operational invariants

- **Tag creation restricted to repo admins.** Configured via the
  GitHub tag-protection rule on `pub-*`.
- **CI must be green before deploy.** The `deploy` job in
  `publish.yml` depends on `validate`, which runs
  `ckl verify-publication --strict`.
- **Rollback is operator-driven.** Use
  `gh workflow run publish.yml -f mode=rollback -f tag=pub-vX.Y.Z`
  to re-deploy a previous tag. The workflow re-verifies before
  redeploying.
- **No force-push to `main`.** The `publishers/` tree is append-only
  across `pub-v*` tags; corrections go through a new patch tag.

## Cache strategy

GitHub Pages serves all files with `Cache-Control: max-age=600` and an
ETag. Subscribers use conditional GET, so re-fetches return 304
within seconds. See [`docs/cache-strategy.md`](./docs/cache-strategy.md)
for the full rationale and the planned Cloudflare migration path.

## License

This repository uses dual licensing:

- **Code** (workflows, scripts, build tooling) — Apache License 2.0.
  See [`LICENSE-CODE`](./LICENSE-CODE).
- **Content** (published knowledge slices in `publishers/koslab/`) —
  Creative Commons Attribution 4.0 International. See
  [`LICENSE-CONTENT`](./LICENSE-CONTENT).

By subscribing to or redistributing KOSLAB publications, you agree to
attribute KOSLAB and preserve the signed `publisher_cert.cbor` so
downstream consumers can re-verify.
