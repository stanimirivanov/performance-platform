"""Reusable enum mappers with safe defaults."""

from __future__ import annotations

from typing import Generic, TypeVar

from perfeng.generated.run_metadata import Profile, Status, Tool, Trigger, Type

E = TypeVar("E")


class EnumMapper(Generic[E]):
    """Case‑insensitive string‑to‑enum mapper."""

    def __init__(self, mapping: dict[str, E], default: E) -> None:
        self._mapping = {k.lower(): v for k, v in mapping.items()}
        self._default = default

    def map(self, value: str) -> E:
        return self._mapping.get(value.lower(), self._default)


STATUS_MAPPER = EnumMapper[Status](
    {
        "created": Status.CREATED,
        "validating": Status.VALIDATING,
        "provisioning": Status.PROVISIONING,
        "warming_up": Status.WARMING_UP,
        "running": Status.RUNNING,
        "collecting": Status.COLLECTING,
        "analyzing": Status.ANALYZING,
        "reporting": Status.REPORTING,
        "completed": Status.COMPLETED,
        "invalid": Status.INVALID,
        "aborted": Status.ABORTED,
        "infrastructure_failure": Status.INFRASTRUCTURE_FAILURE,
        "test_failure": Status.TEST_FAILURE,
        "inconclusive": Status.INCONCLUSIVE,
    },
    Status.CREATED,
)

PROFILE_MAPPER = EnumMapper[Profile](
    {
        "smoke": Profile.smoke,
        "average": Profile.average,
        "regression": Profile.regression,
        "stress": Profile.stress,
        "capacity": Profile.capacity,
        "soak": Profile.soak,
    },
    Profile.regression,
)

TRIGGER_MAPPER = EnumMapper[Trigger](
    {
        "manual": Trigger.manual,
        "ci": Trigger.ci,
        "schedule": Trigger.schedule,
        "bisect": Trigger.bisect,
        "release": Trigger.release,
    },
    Trigger.manual,
)

TOOL_MAPPER = EnumMapper[Tool](
    {
        "k6": Tool.k6,
        "playwright": Tool.playwright,
        "kube-burner": Tool.kube_burner,
        "benchmark-operator": Tool.benchmark_operator,
    },
    Tool.k6,
)

TYPE_MAPPER = EnumMapper[Type](
    {
        "api": Type.api,
        "browser": Type.browser,
        "kubernetes": Type.kubernetes,
        "infrastructure": Type.infrastructure,
    },
    Type.api,
)
