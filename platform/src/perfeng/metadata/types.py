"""Canonical type aliases used across the metadata package."""

from __future__ import annotations

from typing import Any, TypeAlias

# Feature flags for application configuration.
# The generated Pydantic model `Application.featureFlags` expects
# `dict[str, str | bool | float | None]`, so we standardize on that.
FeatureFlags: TypeAlias = dict[str, bool | str | float | None]

# Candidate feature flags are more permissive (can contain arrays, etc.)
AnyFeatureFlags: TypeAlias = dict[str, Any]

# Database size is represented as a string (e.g., "10GB")
DatabaseSize: TypeAlias = str

# Fingerprint excludes list/tuple – use tuple for immutability
FingerprintExcludes: TypeAlias = tuple[str, ...]
