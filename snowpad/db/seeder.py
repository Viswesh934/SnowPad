"""Database seeder with realistic engineering events, hotfixes, and telemetry."""

from datetime import datetime, timedelta
import random
from snowpad.core.models import (
    Actor,
    DebtSeverity,
    DecisionRecord,
    EventType,
    MetricObservation,
    PulseEvent,
    ScopeStatus,
)
from snowpad.db.connection import init_db
from snowpad.db.repository import SnowPadRepository


def seed_demo_data(repo: SnowPadRepository) -> None:
    """Populates DuckDB with a rich, realistic engineering dataset for reviews & radar."""
    init_db(repo.db_path)

    # 1. Seed Actors
    actors = [
        Actor(
            id="alex_chen",
            name="Alex Chen",
            role="Staff Backend Engineer",
            email="alex.chen@snowpad.internal",
            team="Core Infrastructure",
        ),
        Actor(
            id="maya_patel",
            name="Maya Patel",
            role="Senior Systems Engineer",
            email="maya.patel@snowpad.internal",
            team="Checkout & Payments",
        ),
        Actor(
            id="sam_torres",
            name="Sam Torres",
            role="DevOps / SRE Lead",
            email="sam.torres@snowpad.internal",
            team="Platform Reliability",
        ),
        Actor(
            id="jordan_lee",
            name="Jordan Lee",
            role="Fullstack Engineer",
            email="jordan.lee@snowpad.internal",
            team="Growth & Onboarding",
        ),
    ]

    for actor in actors:
        repo.save_actor(actor)

    now = datetime.utcnow()

    # 2. Seed Realistic Events & Correlated Metrics
    scenarios = [
        # Alex Chen: Brilliant firefighter who carries tech debt
        {
            "event": PulseEvent(
                id="evt_hotfix_001",
                actor_id="alex_chen",
                event_type=EventType.HOTFIX,
                title="Bypass cache layer on cart race condition",
                description="Hotfix deployed directly during flash sale outage to bypass corrupted Redis hashes.",
                commit_hash="a1f89bc",
                service_name="cart-service",
                scope_status=ScopeStatus.INSIDE_CIRCLE,
                scope_distance=0.35,
                tech_debt_flag=True,
                tech_debt_severity=DebtSeverity.HIGH,
                rationale="Immediate mitigation during 2 AM P0 incident. Redis hash desync fixed with direct DB query.",
                created_at=now - timedelta(days=21),
            ),
            "metric": MetricObservation(
                id="met_001",
                event_id="evt_hotfix_001",
                metric_name="p95_response_time_ms",
                service_name="cart-service",
                endpoint="/api/v1/cart/checkout",
                baseline_value=320.0,
                observed_value=165.0,
                delta_value=-155.0,
                unit="ms",
                measured_at=now - timedelta(days=21),
            ),
            "decision": DecisionRecord(
                id="dec_001",
                event_id="evt_hotfix_001",
                author_id="alex_chen",
                discussion_summary="Flagged in #eng-war-room: Direct DB query strains PostgreSQL pool. Must rewrite with Redis distributed lock.",
                resolution="SCHEDULE_REFACTOR",
                target_sprint="Sprint-42",
                ttl_days=14,
                created_at=now - timedelta(days=20),
            ),
        },
        {
            "event": PulseEvent(
                id="evt_hotfix_002",
                actor_id="alex_chen",
                event_type=EventType.HOTFIX,
                title="Hardcode fallback foreign exchange rate",
                description="Third-party FX provider returned 504 Gateway Timeout; hotfixed with static fallback rates.",
                commit_hash="c3e901a",
                service_name="billing-service",
                scope_status=ScopeStatus.INSIDE_CIRCLE,
                scope_distance=0.48,
                tech_debt_flag=True,
                tech_debt_severity=DebtSeverity.MEDIUM,
                rationale="Prevented checkout abandonment during upstream API failure.",
                created_at=now - timedelta(days=12),
            ),
            "metric": MetricObservation(
                id="met_002",
                event_id="evt_hotfix_002",
                metric_name="error_rate_pct",
                service_name="billing-service",
                endpoint="/api/v1/pay",
                baseline_value=8.4,
                observed_value=0.05,
                delta_value=-8.35,
                unit="%",
                measured_at=now - timedelta(days=12),
            ),
            "decision": None,
        },
        {
            "event": PulseEvent(
                id="evt_opt_003",
                actor_id="alex_chen",
                event_type=EventType.PERF_OPTIMIZATION,
                title="Compound index on orders(user_id, status, created_at)",
                description="Analyzed slow query log; added concurrent composite index resolving p99 latency spike.",
                commit_hash="f5d210b",
                service_name="order-service",
                scope_status=ScopeStatus.INSIDE_CIRCLE,
                scope_distance=0.15,
                tech_debt_flag=False,
                tech_debt_severity=DebtSeverity.NONE,
                rationale="Proactive query plan optimization.",
                created_at=now - timedelta(days=5),
            ),
            "metric": MetricObservation(
                id="met_003",
                event_id="evt_opt_003",
                metric_name="p99_response_time_ms",
                service_name="order-service",
                endpoint="/api/v1/orders/history",
                baseline_value=480.0,
                observed_value=72.0,
                delta_value=-408.0,
                unit="ms",
                measured_at=now - timedelta(days=5),
            ),
            "decision": None,
        },
        # Maya Patel: High focus, major latency saver, minimal debt
        {
            "event": PulseEvent(
                id="evt_opt_004",
                actor_id="maya_patel",
                event_type=EventType.PERF_OPTIMIZATION,
                title="Pipelined Redis queries for inventory validation",
                description="Replaced sequential single-item Redis lookups with batched MGET & pipeline execution.",
                commit_hash="78ab44c",
                service_name="inventory-service",
                scope_status=ScopeStatus.INSIDE_CIRCLE,
                scope_distance=0.20,
                tech_debt_flag=False,
                tech_debt_severity=DebtSeverity.NONE,
                rationale="Reduced network roundtrips from 18ms per cart to under 2ms.",
                created_at=now - timedelta(days=18),
            ),
            "metric": MetricObservation(
                id="met_004",
                event_id="evt_opt_004",
                metric_name="p95_response_time_ms",
                service_name="inventory-service",
                endpoint="/api/v1/inventory/batch-check",
                baseline_value=190.0,
                observed_value=28.0,
                delta_value=-162.0,
                unit="ms",
                measured_at=now - timedelta(days=18),
            ),
            "decision": None,
        },
        {
            "event": PulseEvent(
                id="evt_hotfix_005",
                actor_id="maya_patel",
                event_type=EventType.HOTFIX,
                title="Fix float precision rounding error in VAT calculation",
                description="Hotfix using Decimal arithmetic preventing 1-cent discrepancy in euro billing.",
                commit_hash="99bb12e",
                service_name="billing-service",
                scope_status=ScopeStatus.INSIDE_CIRCLE,
                scope_distance=0.40,
                tech_debt_flag=False,
                tech_debt_severity=DebtSeverity.NONE,
                rationale="Critical financial compliance issue discovered during end-of-month reconcile.",
                created_at=now - timedelta(days=8),
            ),
            "metric": MetricObservation(
                id="met_005",
                event_id="evt_hotfix_005",
                metric_name="audit_error_count",
                service_name="billing-service",
                endpoint="/api/v1/invoices/generate",
                baseline_value=142.0,
                observed_value=0.0,
                delta_value=-142.0,
                unit="count",
                measured_at=now - timedelta(days=8),
            ),
            "decision": None,
        },
        # Sam Torres: Infrastructure guardian
        {
            "event": PulseEvent(
                id="evt_conf_006",
                actor_id="sam_torres",
                event_type=EventType.CONFIG_CHANGE,
                title="Tune connection pool max_overflow and pool_recycle",
                description="Resolved sporadic PostgreSQL connection exhaustion under high concurrency.",
                commit_hash="ee41029",
                service_name="api-gateway",
                scope_status=ScopeStatus.INSIDE_CIRCLE,
                scope_distance=0.30,
                tech_debt_flag=False,
                tech_debt_severity=DebtSeverity.NONE,
                rationale="Eliminated connection spike drops.",
                created_at=now - timedelta(days=15),
            ),
            "metric": MetricObservation(
                id="met_006",
                event_id="evt_conf_006",
                metric_name="p99_response_time_ms",
                service_name="api-gateway",
                endpoint="/api/v1/health/gateway",
                baseline_value=650.0,
                observed_value=95.0,
                delta_value=-555.0,
                unit="ms",
                measured_at=now - timedelta(days=15),
            ),
            "decision": None,
        },
        # Jordan Lee: High churn, off-scope noise that drifted outside the circle
        {
            "event": PulseEvent(
                id="evt_adhoc_007",
                actor_id="jordan_lee",
                event_type=EventType.AD_HOC_EXPERIMENT,
                title="Ad-hoc CSS animation refactor on internal admin drawer",
                description="Spontaneous styling overhaul of internal debug drawer during active sprint.",
                commit_hash="11ba90c",
                service_name="admin-portal",
                scope_status=ScopeStatus.OUTSIDE_CIRCLE,
                scope_distance=1.65,
                tech_debt_flag=True,
                tech_debt_severity=DebtSeverity.LOW,
                rationale="Personal whim improvement; not aligned with current sprint goals.",
                created_at=now - timedelta(days=10),
            ),
            "metric": MetricObservation(
                id="met_007",
                event_id="evt_adhoc_007",
                metric_name="bundle_size_kb",
                service_name="admin-portal",
                endpoint="/assets/bundle.js",
                baseline_value=240.0,
                observed_value=285.0,
                delta_value=45.0,
                unit="kb",
                measured_at=now - timedelta(days=10),
            ),
            "decision": DecisionRecord(
                id="dec_002",
                event_id="evt_adhoc_007",
                author_id="jordan_lee",
                discussion_summary="Discussed with Lead: Outside core sprint scope. Reverted from main branch, moved to feature branch.",
                resolution="QUARANTINE",
                target_sprint="Backlog",
                ttl_days=30,
                created_at=now - timedelta(days=9),
            ),
        },
        {
            "event": PulseEvent(
                id="evt_hotfix_008",
                actor_id="jordan_lee",
                event_type=EventType.HOTFIX,
                title="Quick regex bypass on promo code validation",
                description="Unindexed regex match added directly to route handler on a whim to allow promotional character.",
                commit_hash="44dc77e",
                service_name="promo-service",
                scope_status=ScopeStatus.OUTSIDE_CIRCLE,
                scope_distance=1.40,
                tech_debt_flag=True,
                tech_debt_severity=DebtSeverity.MEDIUM,
                rationale="Customer requested hyphen in coupon code; hotfixed without validation schema update.",
                created_at=now - timedelta(days=4),
            ),
            "metric": MetricObservation(
                id="met_008",
                event_id="evt_hotfix_008",
                metric_name="p95_response_time_ms",
                service_name="promo-service",
                endpoint="/api/v1/coupons/apply",
                baseline_value=45.0,
                observed_value=68.0,
                delta_value=23.0,
                unit="ms",
                measured_at=now - timedelta(days=4),
            ),
            "decision": None,
        },
    ]

    for item in scenarios:
        repo.save_pulse_event(item["event"])
        if item["metric"]:
            repo.save_metric_observation(item["metric"])
        if item["decision"]:
            repo.save_decision(item["decision"])
