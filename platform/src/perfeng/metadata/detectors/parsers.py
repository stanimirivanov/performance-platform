"""Resource string parsers."""

from __future__ import annotations

import re


class ResourceParser:
    """Parse Kubernetes resource quantity strings."""

    _MEMORY_PATTERN = re.compile(r"^(\d+(?:\.\d+)?)\s*(Ki|Mi|Gi|Ti)?$", re.IGNORECASE)

    _MEMORY_MULTIPLIERS: dict[str, float] = {
        "ki": 1.0 / (1024**2),
        "mi": 1.0 / 1024,
        "gi": 1.0,
        "ti": 1024.0,
    }

    @staticmethod
    def cpu_count(cpu_str: str | None) -> int | None:
        """Parse a CPU quantity string (e.g. "1500m" or "2").

        Returns whole cores. Fractional cores from millicores are truncated.
        """
        if not cpu_str:
            return None
        try:
            if cpu_str.endswith("m"):
                return int(cpu_str[:-1]) // 1000
            return int(cpu_str)
        except ValueError:
            return None

    @classmethod
    def memory_gib(cls, memory_str: str | None) -> float | None:
        """Parse a memory quantity string (e.g. "16Gi", "512Mi", "1.5Gi").

        Returns gibibytes (GiB).
        """
        if not memory_str:
            return None
        match = cls._MEMORY_PATTERN.match(memory_str.strip())
        if not match:
            return None
        value = float(match.group(1))
        unit = (match.group(2) or "").lower()
        return value * cls._MEMORY_MULTIPLIERS.get(unit, 1.0 / (1024**3))
