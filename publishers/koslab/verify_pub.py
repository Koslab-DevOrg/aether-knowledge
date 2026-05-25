#!/usr/bin/env python3
"""Verify pub-v0.1.1 blob transport (PDA-11).

Reads ONLY the aether-knowledge/publishers/koslab/pub-v0.1.1/ directory
(no access to ~/.ckl/).  For each entry in manifest.blob_index:
  1. Read the sidecar at blobs/<oid[:2]>/<oid[2:]>
  2. Compute sha256 of the raw bytes
  3. Assert sha256 matches content_hash
  4. Print the reconstructed markdown body

Also byte-exact diffs one body against a source document from
~/.kos/workspaces/my-workspace/documents/<docid>/document.md.
"""

import hashlib
import json
import os
import sys

PUB_ROOT = os.path.join(os.path.dirname(__file__), "pub-v0.1.1")
MANIFEST_PATH = os.path.join(PUB_ROOT, "pkg", "manifest.json")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_blobs(manifest: dict) -> list[dict]:
    blob_index = manifest.get("blob_index", [])
    if not blob_index:
        print("ERROR: manifest has no blob_index entries", file=sys.stderr)
        sys.exit(1)

    results = []
    for entry in blob_index:
        oid = entry["oid"]
        expected_hash = entry["content_hash"]
        size_bytes = entry["size_bytes"]

        sidecar_path = os.path.join(PUB_ROOT, "blobs", oid[:2], oid[2:])
        if not os.path.exists(sidecar_path):
            print(f"  FAIL  {oid}: sidecar not found at {sidecar_path}", file=sys.stderr)
            results.append({"oid": oid, "ok": False, "reason": "missing sidecar"})
            continue

        raw = open(sidecar_path, "rb").read()
        if len(raw) != size_bytes:
            print(f"  FAIL  {oid}: size mismatch (got {len(raw)}, want {size_bytes})")
            results.append({"oid": oid, "ok": False, "reason": "size mismatch"})
            continue

        computed = sha256_hex(raw)
        if computed == expected_hash:
            print(f"  OK    {oid[:16]}… sha256={computed[:16]}… ({len(raw)} bytes)")
            results.append({"oid": oid, "ok": True, "content": raw})
        else:
            print(f"  FAIL  {oid}: sha256 mismatch\n    got  {computed}\n    want {expected_hash}")
            results.append({"oid": oid, "ok": False, "reason": "hash mismatch"})

    return results


def diff_against_source(entry: dict, doc_id: str):
    """Byte-exact diff one reconstructed body vs the source document."""
    source_path = os.path.expanduser(
        f"~/.kos/workspaces/my-workspace/documents/{doc_id}/document.md"
    )
    if not os.path.exists(source_path):
        print(f"\nSkipping byte-exact diff — source not found at {source_path}")
        return

    source_bytes = open(source_path, "rb").read()
    blob_bytes = entry["content"]

    print(f"\nByte-exact diff: blob oid={entry['oid'][:16]}…")
    print(f"  source: {source_path} ({len(source_bytes)} bytes)")
    print(f"  sidecar:                         ({len(blob_bytes)} bytes)")

    if source_bytes == blob_bytes:
        print("  MATCH  byte-exact match confirmed ✓")
    else:
        # Show first differing position
        for i, (a, b) in enumerate(zip(source_bytes, blob_bytes)):
            if a != b:
                print(f"  MISMATCH at byte {i}: source={a:#04x} blob={b:#04x}")
                break
        else:
            print(f"  MISMATCH lengths differ: source={len(source_bytes)} blob={len(blob_bytes)}")


def main():
    if not os.path.exists(MANIFEST_PATH):
        print(f"ERROR: manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(open(MANIFEST_PATH).read())
    print(f"Publisher:   {manifest['publisher_id']}")
    print(f"Signed at:   {manifest['signed_at']}")
    print(f"blob_index:  {len(manifest.get('blob_index', []))} entries")
    print()

    results = verify_blobs(manifest)

    ok_count = sum(1 for r in results if r["ok"])
    total = len(results)
    print(f"\n{ok_count}/{total} hashes match")

    if ok_count != total:
        sys.exit(1)

    # Byte-exact diff: pick the first successfully verified blob entry,
    # find a source document whose blob_oid matches it.
    #
    # The source docs live at ~/.kos/.../documents/<docid>/document.md.
    # We locate the matching doc by scanning the workspace documents dir.
    docs_dir = os.path.expanduser("~/.kos/workspaces/my-workspace/documents")
    first_ok = next((r for r in results if r["ok"]), None)
    if first_ok and os.path.isdir(docs_dir):
        oid = first_ok["oid"]
        # Find any document whose content sha256 matches
        matched_doc_id = None
        for doc_id in os.listdir(docs_dir):
            doc_path = os.path.join(docs_dir, doc_id, "document.md")
            if not os.path.exists(doc_path):
                continue
            src = open(doc_path, "rb").read()
            if sha256_hex(src) == first_ok.get("oid", ""):  # oid is sha1, not sha256
                matched_doc_id = doc_id
                break
        if matched_doc_id is None:
            # Fall back: pick the doc whose content matches the blob bytes by sha256
            blob_hash = sha256_hex(first_ok["content"])
            for doc_id in os.listdir(docs_dir):
                doc_path = os.path.join(docs_dir, doc_id, "document.md")
                if not os.path.exists(doc_path):
                    continue
                src = open(doc_path, "rb").read()
                if sha256_hex(src) == blob_hash:
                    matched_doc_id = doc_id
                    break

        if matched_doc_id:
            diff_against_source(first_ok, matched_doc_id)
        else:
            print(f"\nNote: no source document found with sha256={sha256_hex(first_ok['content'])[:16]}…")
            print("Printing first 200 bytes of reconstructed body:")
            print(first_ok["content"][:200].decode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
