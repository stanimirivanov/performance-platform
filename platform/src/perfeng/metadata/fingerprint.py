"""Generate environment fingerprints."""

import hashlib


def generate_fingerprint(
    cluster_name: str,
    k8s_version: str | None,
    node_os: str,
    container_runtime: str | None,
    excludes: list[str] | None = None,
) -> str:
    """Generate a SHA256 fingerprint from environment characteristics."""
    parts = [
        cluster_name or "",
        k8s_version or "",
        node_os or "",
        container_runtime or "",
    ]
    if excludes:
        parts = [p for p in parts if p not in excludes]
    fingerprint_string = "|".join(parts)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()
