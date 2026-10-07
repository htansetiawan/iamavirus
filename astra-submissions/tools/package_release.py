#!/usr/bin/env python3
"""Package Astra at max(Fable archive major versions) + 1, without overwrites."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ASTRA = ROOT / "astra-submissions"


def next_version():
    versions = []
    for path in (ROOT / "fable-submissions").glob("*.zip"):
        match = re.fullmatch(r"iamavirus-v(\d+)(?:\.\d+)?-(?:cpp|hybrid|neural)\.zip", path.name)
        if match:
            versions.append(int(match[1]))
    if not versions:
        raise RuntimeError("No numbered Fable archives found; cannot establish the +1 rule")
    return max(versions) + 1


def main():
    version = next_version()
    output = ASTRA / f"iamavirus-v{version}-hybrid.zip"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    source = ASTRA / "implementation"
    origin = json.loads((ASTRA / "implementation-origin.json").read_text())
    names = sorted(origin["initial_files_sha256"])
    names += ["RELEASE.md"]
    # Explicit original-source allowlist: no binaries, caches, or credentials.
    content = {name: (source / name).read_bytes() for name in names}
    for name, expected in origin["initial_files_sha256"].items():
        if name.startswith("model/"):
            assert hashlib.sha256(content[name]).hexdigest() == expected, name
    assert b"FOW_MODE:-hybrid" in content["run.sh"]
    metadata = {
        "author": "Astra", "version": version, "fable_version": version - 1,
        "numbering_rule": "max(fable-submissions numbered archive major versions) + 1",
        "mode": "hybrid", "basis_archive_sha256": origin["archive_sha256"],
        "model": "unchanged Stage A v1; no PPO weights",
        "files_sha256": {n: hashlib.sha256(data).hexdigest() for n, data in content.items()},
    }
    content["astra-release.json"] = (json.dumps(metadata, indent=2) + "\n").encode()
    fd, temporary = tempfile.mkstemp(prefix="astra-package-", suffix=".zip", dir=ASTRA)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(content.items()):
                entry = zipfile.ZipInfo(name, date_time=(2026, 10, 7, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = (0o100755 if name.endswith(".sh") else 0o100644) << 16
                archive.writestr(entry, data)
        if next_version() != version:
            raise RuntimeError("Fable published a newer version while packaging; retry")
        os.link(temporary, output)  # atomic publication, fails if output exists
    finally:
        Path(temporary).unlink(missing_ok=True)
    metadata["archive"] = output.name
    metadata["archive_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    (ASTRA / f"v{version}-manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({k: metadata[k] for k in ("archive", "version", "fable_version", "archive_sha256")}, indent=2))


if __name__ == "__main__":
    main()
