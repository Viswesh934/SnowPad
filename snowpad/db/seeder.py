"""Database seeder with realistic chat signals, feature proposals, and scope debates."""

from datetime import datetime, timedelta
from snowpad.core.models import (
    Actor,
    ChatSignal,
    MetricObservation,
    ScopeStatus,
    SignalResolution,
    SignalType,
)
from snowpad.db.connection import init_db
from snowpad.db.repository import SnowPadRepository


def seed_demo_data(repo: SnowPadRepository) -> None:
    """Populates DuckDB with a rich, realistic dataset of uncertain chat discussions."""
    init_db(repo.db_path)

    # 1. Seed Actors (Devs, PMs, Architects)
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
            role="Product Architect",
            email="maya.patel@snowpad.internal",
            team="Checkout & Payments",
        ),
        Actor(
            id="sam_torres",
            name="Sam Torres",
            role="Lead Product Manager",
            email="sam.torres@snowpad.internal",
            team="Platform Strategy",
        ),
        Actor(
            id="jordan_lee",
            name="Jordan Lee",
            role="Frontend Engineer",
            email="jordan.lee@snowpad.internal",
            team="Growth & Onboarding",
        ),
    ]

    for actor in actors:
        repo.save_actor(actor)

    now = datetime.utcnow()

    # 2. Seed Realistic Chat Signals
    scenarios = [
        # Maya Patel: High-certainty feature proposals that made it inside the circle
        {
            "signal": ChatSignal(
                id="sig_feat_001",
                actor_id="maya_patel",
                signal_type=SignalType.FEATURE_PROPOSAL,
                title="Batched Multi-Currency Settlement Engine",
                summary="Proposed in Slack #product-ideas: Consolidate euro/dollar payment settlements into single batch run.",
                origin_channel="#product-ideas",
                uncertainty_score=0.15,
                scope_status=ScopeStatus.INSIDE_CIRCLE,
                scope_distance=0.25,
                estimated_kpi_impact="Reduces Stripe fee churn by 4.2% & cuts p95 API latency by 120ms.",
                resolution=SignalResolution.APPROVED_FOR_SPRINT,
                target_sprint="Sprint-42",
                created_at=now - timedelta(days=14),
            ),
            "metric": MetricObservation(
                id="met_001",
                signal_id="sig_feat_001",
                metric_name="p95_response_time_ms",
                service_name="billing-service",
                endpoint="/api/v1/settlements/batch",
                baseline_value=280.0,
                observed_value=158.0,
                delta_value=-122.0,
                unit="ms",
                measured_at=now - timedelta(days=14),
            ),
        },
        # Alex Chen: Architectural debate that was resolved & implemented
        {
            "signal": ChatSignal(
                id="sig_arch_002",
                actor_id="alex_chen",
                signal_type=SignalType.ARCH_DEBATE,
                title="Replace PostgreSQL Row-Level Lock with Redis Redlock",
                summary="Spirited debate in #backend-core: Row locks were causing cascading timeouts during flash sales.",
                origin_channel="#backend-core",
                uncertainty_score=0.30,
                scope_status=ScopeStatus.INSIDE_CIRCLE,
                scope_distance=0.40,
                estimated_kpi_impact="Eliminated 504 gateway timeouts on /checkout.",
                resolution=SignalResolution.APPROVED_FOR_SPRINT,
                target_sprint="Sprint-41",
                created_at=now - timedelta(days=10),
            ),
            "metric": MetricObservation(
                id="met_002",
                signal_id="sig_arch_002",
                metric_name="p99_response_time_ms",
                service_name="cart-service",
                endpoint="/api/v1/checkout/lock",
                baseline_value=720.0,
                observed_value=85.0,
                delta_value=-635.0,
                unit="ms",
                measured_at=now - timedelta(days=10),
            ),
        },
        # Sam Torres (PM): Active Scope Pivot debate currently borderline (needs resolution)
        {
            "signal": ChatSignal(
                id="sig_piv_003",
                actor_id="sam_torres",
                signal_type=SignalType.SCOPE_PIVOT,
                title="Deprecate Multi-step Onboarding Wizard in favor of 1-Click Social Sign-in",
                summary="Discussed in #growth-experiments: Drop phone verification step to boost conversion rate.",
                origin_channel="#growth-experiments",
                uncertainty_score=0.55,
                scope_status=ScopeStatus.BORDERLINE_DEBATE,
                scope_distance=0.85,
                estimated_kpi_impact="+18% signup conversion, but unknown fraud risk impact.",
                resolution=SignalResolution.UNDER_DEBATE,
                target_sprint="Backlog",
                created_at=now - timedelta(days=3),
            ),
            "metric": None,
        },
        # Alex Chen: Another pending architecture debate in chat
        {
            "signal": ChatSignal(
                id="sig_arch_004",
                actor_id="alex_chen",
                signal_type=SignalType.ARCH_DEBATE,
                title="Migrate audit log streaming from SQS to Apache Kafka",
                summary="Discussed in #eng-war-room: SQS costs spiking on 10k req/sec peak. Proposed Kafka sidecar.",
                origin_channel="#eng-war-room",
                uncertainty_score=0.60,
                scope_status=ScopeStatus.BORDERLINE_DEBATE,
                scope_distance=0.92,
                estimated_kpi_impact="Estimated $1,400/mo AWS cost reduction; requires 2-week migration effort.",
                resolution=SignalResolution.UNDER_DEBATE,
                target_sprint="Sprint-43",
                created_at=now - timedelta(days=2),
            ),
            "metric": None,
        },
        # Jordan Lee: Casual whims that were safely parked outside the circle
        {
            "signal": ChatSignal(
                id="sig_whim_005",
                actor_id="jordan_lee",
                signal_type=SignalType.CASUAL_WHIM,
                title="Lottie Particle Confetti Animation on Order Success",
                summary="Casual message in #frontend-chatter: 'Hey, wouldn't it be cute if confetti burst on every purchase?'",
                origin_channel="#frontend-chatter",
                uncertainty_score=0.88,
                scope_status=ScopeStatus.OUTSIDE_CIRCLE,
                scope_distance=1.60,
                estimated_kpi_impact="Adds 140kb to critical client bundle; zero proven revenue lift.",
                resolution=SignalResolution.PARKED_AS_WHIM,
                target_sprint=None,
                created_at=now - timedelta(days=8),
            ),
            "metric": MetricObservation(
                id="met_005",
                signal_id="sig_whim_005",
                metric_name="bundle_size_kb",
                service_name="web-client",
                endpoint="/assets/checkout.js",
                baseline_value=210.0,
                observed_value=350.0,
                delta_value=140.0,
                unit="kb",
                measured_at=now - timedelta(days=8),
            ),
        },
        {
            "signal": ChatSignal(
                id="sig_whim_006",
                actor_id="jordan_lee",
                signal_type=SignalType.CASUAL_WHIM,
                title="Custom Neon Dark Theme Toggle for Admin Panel",
                summary="Chat proposal in #general: 'Thinking of redesigning the internal admin panel theme this afternoon.'",
                origin_channel="#general",
                uncertainty_score=0.95,
                scope_status=ScopeStatus.OUTSIDE_CIRCLE,
                scope_distance=1.85,
                estimated_kpi_impact="High distraction risk; no customer impact.",
                resolution=SignalResolution.PARKED_AS_WHIM,
                target_sprint=None,
                created_at=now - timedelta(days=5),
            ),
            "metric": None,
        },
        # Sam Torres: Legitimate feature proposal approved into sprint
        {
            "signal": ChatSignal(
                id="sig_feat_007",
                actor_id="sam_torres",
                signal_type=SignalType.FEATURE_PROPOSAL,
                title="Real-time Webhook Event Dispatcher for Enterprise Tier",
                summary="Discussed in #enterprise-sales: Top 3 enterprise prospects need outbound webhooks on order fulfillment.",
                origin_channel="#enterprise-sales",
                uncertainty_score=0.20,
                scope_status=ScopeStatus.INSIDE_CIRCLE,
                scope_distance=0.35,
                estimated_kpi_impact="Directly unblocks $180k ARR enterprise pipeline.",
                resolution=SignalResolution.APPROVED_FOR_SPRINT,
                target_sprint="Sprint-42",
                created_at=now - timedelta(days=12),
            ),
            "metric": None,
        },
    ]

    for item in scenarios:
        repo.save_chat_signal(item["signal"])
        if item["metric"]:
            repo.save_metric_observation(item["metric"])
