"""Domain models for SnowPad's event ledger and Circle-of-Scope intelligence."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ScopeStatus(str, Enum):
    """Classification of an event relative to the Circle of Scope."""
    INSIDE_CIRCLE = "INSIDE_CIRCLE"      # Critical SLA/KPI impact; core business focus
    OUTSIDE_CIRCLE = "OUTSIDE_CIRCLE"    # Off-scope churn, unindexed hack, distraction
    BORDERLINE = "BORDERLINE"            # Requires team discussion / triage review


class EventType(str, Enum):
    """Types of operational engineering events."""
    HOTFIX = "HOTFIX"
    INCIDENT_PATCH = "INCIDENT_PATCH"
    PERF_OPTIMIZATION = "PERF_OPTIMIZATION"
    REFACTOR = "REFACTOR"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    AD_HOC_EXPERIMENT = "AD_HOC_EXPERIMENT"


class DebtSeverity(str, Enum):
    """Severity rating for incurred technical debt."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Actor(BaseModel):
    """An individual contributor, engineer, PM, or operator mapped in SnowPad."""
    id: str
    name: str
    role: str
    email: str
    team: str = "Core Engineering"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PulseEvent(BaseModel):
    """A developer action, spontaneous hotfix, or code change mapped to scope & metrics."""
    id: str
    actor_id: str
    event_type: EventType = EventType.HOTFIX
    title: str
    description: str
    commit_hash: Optional[str] = None
    service_name: str = "api-gateway"
    scope_status: ScopeStatus = ScopeStatus.INSIDE_CIRCLE
    scope_distance: float = Field(
        default=0.5,
        description="Radial distance from core SLA center: <= 1.0 is inside circle, > 1.0 outside"
    )
    tech_debt_flag: bool = False
    tech_debt_severity: DebtSeverity = DebtSeverity.NONE
    rationale: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MetricObservation(BaseModel):
    """Telemetry & performance metric measurement tied to an event."""
    id: str
    event_id: Optional[str] = None
    metric_name: str = "p95_response_time_ms"
    service_name: str = "api-gateway"
    endpoint: str = "/api/v1/checkout"
    baseline_value: float
    observed_value: float
    delta_value: float = Field(description="Negative means improvement, positive means regression")
    unit: str = "ms"
    measured_at: datetime = Field(default_factory=datetime.utcnow)


class DecisionRecord(BaseModel):
    """Team triage outcome on an ad-hoc fix or debt item discussed in chat."""
    id: str
    event_id: str
    author_id: str
    discussion_summary: str
    resolution: str = "SCHEDULE_REFACTOR"  # ACCEPT_DEBT, SCHEDULE_REFACTOR, QUARANTINE, RESOLVED
    target_sprint: Optional[str] = None
    ttl_days: int = 14
    created_at: datetime = Field(default_factory=datetime.utcnow)
