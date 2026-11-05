"""Domain models for SnowPad's Chat Uncertainty Ledger and Circle-of-Scope Intelligence."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ScopeStatus(str, Enum):
    """Classification of a signal relative to the Circle of Scope."""
    INSIDE_CIRCLE = "INSIDE_CIRCLE"      # Confirmed scope, verified SLA/KPI alignment
    BORDERLINE_DEBATE = "BORDERLINE"     # Active thread debate; high uncertainty, needs decision
    OUTSIDE_CIRCLE = "OUTSIDE_CIRCLE"    # Fleeting whim, off-scope noise, parked outside


class SignalType(str, Enum):
    """Categories of uncertain discussions and ideas circulating in team chat."""
    FEATURE_PROPOSAL = "FEATURE_PROPOSAL"   # "What if we add bulk CSV export?"
    SCOPE_PIVOT = "SCOPE_PIVOT"             # "Let's redesign checkout into a single-page modal"
    ARCH_DEBATE = "ARCH_DEBATE"             # "Should we replace Postgres lock with Redis pipeline?"
    HOTFIX_REQUEST = "HOTFIX_REQUEST"       # "Need a quick bypass for rate limit issue"
    CASUAL_WHIM = "CASUAL_WHIM"             # "Can we change the dashboard theme on a whim?"


class SignalResolution(str, Enum):
    """Triage outcome for an uncertain chat item."""
    APPROVED_FOR_SPRINT = "APPROVED_FOR_SPRINT"
    PARKED_AS_WHIM = "PARKED_AS_WHIM"
    UNDER_DEBATE = "UNDER_DEBATE"
    REJECTED = "REJECTED"
    CONVERTED_TO_PRD = "CONVERTED_TO_PRD"


class Actor(BaseModel):
    """An individual contributor, engineer, PM, or leader mapped in SnowPad."""
    id: str
    name: str
    role: str
    email: str
    team: str = "Core Engineering"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatSignal(BaseModel):
    """An uncertain idea, feature proposal, or spontaneous discussion captured from chat."""
    id: str
    actor_id: str
    signal_type: SignalType = SignalType.FEATURE_PROPOSAL
    title: str
    summary: str
    origin_channel: str = "#product-general"
    thread_url: Optional[str] = None
    uncertainty_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="0.0 = Locked/Certain, 1.0 = Highly Ambiguous/Vague Chat"
    )
    scope_status: ScopeStatus = ScopeStatus.BORDERLINE_DEBATE
    scope_distance: float = Field(
        default=0.8,
        description="Radial distance from core circle: <=1.0 Inside, >1.0 Outside"
    )
    estimated_kpi_impact: Optional[str] = None
    resolution: SignalResolution = SignalResolution.UNDER_DEBATE
    target_sprint: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MetricObservation(BaseModel):
    """Telemetry, response time, or business KPI correlated to a signal or feature."""
    id: str
    signal_id: Optional[str] = None
    metric_name: str = "p95_response_time_ms"
    service_name: str = "api-gateway"
    endpoint: str = "/api/v1/orders"
    baseline_value: float
    observed_value: float
    delta_value: float = Field(description="Negative = improvement, positive = regression")
    unit: str = "ms"
    measured_at: datetime = Field(default_factory=datetime.utcnow)
