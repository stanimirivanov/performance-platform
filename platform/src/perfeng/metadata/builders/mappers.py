"""Reusable enum mappers with safe defaults."""

from __future__ import annotations

from typing import Generic, TypeVar

from perfeng.generated.run_metadata import Profile, RunStatus, TestTool, TestType, Trigger

E = TypeVar("E")


class EnumMapper(Generic[E]):
    """Case‑insensitive string‑to‑enum mapper."""

    def __init__(self, mapping: dict[str, E], default: E) -> None:
        self._mapping = {k.lower(): v for k, v in mapping.items()}
        self._default = default

    def map(self, value: str) -> E:
        return self._mapping.get(value.lower(), self._default)


STATUS_MAPPER = EnumMapper[RunStatus](
    {
        "created": RunStatus.CREATED,
        "validating": RunStatus.VALIDATING,
        "provisioning": RunStatus.PROVISIONING,
        "warming_up": RunStatus.WARMING_UP,
        "running": RunStatus.RUNNING,
        "collecting": RunStatus.COLLECTING,
        "analyzing": RunStatus.ANALYZING,
        "reporting": RunStatus.REPORTING,
        "completed": RunStatus.COMPLETED,
        "invalid": RunStatus.INVALID,
        "aborted": RunStatus.ABORTED,
        "infrastructure_failure": RunStatus.INFRASTRUCTURE_FAILURE,
        "test_failure": RunStatus.TEST_FAILURE,
        "inconclusive": RunStatus.INCONCLUSIVE,
    },
    RunStatus.CREATED,
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

TOOL_MAPPER = EnumMapper[TestTool](
    {
        "k6": TestTool.k6,
        "playwright": TestTool.playwright,
        "kube-burner": TestTool.kube_burner,
        "benchmark-operator": TestTool.benchmark_operator,
    },
    TestTool.k6,
)

TYPE_MAPPER = EnumMapper[TestType](
    {
        "api": TestType.api,
        "browser": TestType.browser,
        "kubernetes": TestType.kubernetes,
        "infrastructure": TestType.infrastructure,
    },
    TestType.api,
)
