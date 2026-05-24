# Aether Knowledge — KOSLAB Publisher

L3 knowledge layer publications by **KOSLAB**.

This repository hosts Aether protocol slice packages published under the `koslab` publisher namespace. It is served via GitHub Pages as a static HTTP origin for the Aether T1 Bulk Transport.

- **Origin:** https://aether.koslab.ai
- **Publisher manifest:** [/publishers/koslab/](./publishers/koslab/)
- **Protocol:** Aether v0.4 (CKL)

## Subscribe

From any CKL workspace:

```sh
ckl aether subscribe https://aether.koslab.ai/publishers/koslab/
```

## Publication invariants

- All slice tags follow the pattern `pub-<publisher>-<slice-id>-<version>` and are signed.
- Tag creation/update/deletion is restricted to repository admins.
- The publisher root manifest (`publishers/koslab/manifest.json`) is the only authoritative entrypoint.

## License

Publications are governed by KOSLAB terms. The repository structure is open for inspection.
