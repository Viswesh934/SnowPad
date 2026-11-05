"""DuckDB Schema DDL and Analytical Views for SnowPad's Chat Uncertainty Ledger."""

SCHEMA_DDL = """
-- 1. Actors: Developers, PMs, Designers, and Leaders mapped in SnowPad
CREATE TABLE IF NOT EXISTS actors (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    team VARCHAR NOT NULL DEFAULT 'Core Engineering',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Chat Signals: Uncertain discussions, feature proposals, scope pivots, and whims
CREATE TABLE IF NOT EXISTS chat_signals (
    id VARCHAR PRIMARY KEY,
    actor_id VARCHAR NOT NULL REFERENCES actors(id),
    signal_type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    summary VARCHAR NOT NULL,
    origin_channel VARCHAR NOT NULL DEFAULT '#product-ideas',
    thread_url VARCHAR,
    uncertainty_score DOUBLE NOT NULL DEFAULT 0.5,
    scope_status VARCHAR NOT NULL DEFAULT 'BORDERLINE',
    scope_distance DOUBLE NOT NULL DEFAULT 0.8,
    estimated_kpi_impact VARCHAR,
    resolution VARCHAR NOT NULL DEFAULT 'UNDER_DEBATE',
    target_sprint VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Metric Observations: Telemetry, response times, and KPI impacts
CREATE TABLE IF NOT EXISTS metric_observations (
    id VARCHAR PRIMARY KEY,
    signal_id VARCHAR REFERENCES chat_signals(id),
    metric_name VARCHAR NOT NULL DEFAULT 'p95_response_time_ms',
    service_name VARCHAR NOT NULL DEFAULT 'api-gateway',
    endpoint VARCHAR NOT NULL DEFAULT '/api/v1/orders',
    baseline_value DOUBLE NOT NULL,
    observed_value DOUBLE NOT NULL,
    delta_value DOUBLE NOT NULL,
    unit VARCHAR DEFAULT 'ms',
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytical View 1: Weekly Operational Pulse
CREATE OR REPLACE VIEW v_weekly_pulse AS
SELECT 
    date_trunc('week', s.created_at) AS pulse_week,
    a.id AS actor_id,
    a.name AS actor_name,
    a.role AS actor_role,
    COUNT(s.id) AS total_signals,
    COUNT(CASE WHEN s.signal_type = 'FEATURE_PROPOSAL' THEN 1 END) AS features_count,
    COUNT(CASE WHEN s.signal_type = 'CASUAL_WHIM' THEN 1 END) AS whims_count,
    COUNT(CASE WHEN s.scope_status = 'INSIDE_CIRCLE' THEN 1 END) AS inside_circle_count,
    COUNT(CASE WHEN s.scope_status = 'OUTSIDE_CIRCLE' THEN 1 END) AS outside_circle_count,
    ROUND(AVG(s.uncertainty_score), 2) AS avg_uncertainty,
    ROUND(AVG(COALESCE(m.delta_value, 0.0)), 2) AS avg_latency_delta_ms
FROM actors a
JOIN chat_signals s ON a.id = s.actor_id
LEFT JOIN metric_observations m ON s.id = m.signal_id
GROUP BY 1, 2, 3, 4;

-- Analytical View 2: Contributor Impact & Focus (The "Brag Sheet" & Review view)
CREATE OR REPLACE VIEW v_developer_impact AS
SELECT 
    a.id AS actor_id,
    a.name AS actor_name,
    a.role AS actor_role,
    a.team,
    COUNT(DISTINCT s.id) AS total_contributions,
    COUNT(DISTINCT CASE WHEN s.signal_type = 'FEATURE_PROPOSAL' AND s.resolution = 'APPROVED_FOR_SPRINT' THEN s.id END) AS confirmed_features,
    COUNT(DISTINCT CASE WHEN s.signal_type = 'CASUAL_WHIM' OR s.resolution = 'PARKED_AS_WHIM' THEN s.id END) AS whims_quarantined,
    COUNT(DISTINCT CASE WHEN s.scope_status = 'INSIDE_CIRCLE' THEN s.id END) AS high_impact_circle_count,
    COUNT(DISTINCT CASE WHEN s.scope_status = 'OUTSIDE_CIRCLE' THEN s.id END) AS low_leverage_churn_count,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN s.scope_status = 'INSIDE_CIRCLE' THEN s.id END) / 
        NULLIF(COUNT(DISTINCT s.id), 0), 
        1
    ) AS circle_focus_percentage,
    ROUND(AVG(s.uncertainty_score), 2) AS avg_uncertainty,
    ROUND(COALESCE(SUM(CASE WHEN m.delta_value < 0 THEN ABS(m.delta_value) ELSE 0 END), 0.0), 1) AS total_ms_shaved
FROM actors a
LEFT JOIN chat_signals s ON a.id = s.actor_id
LEFT JOIN metric_observations m ON s.id = m.signal_id
GROUP BY a.id, a.name, a.role, a.team;

-- Analytical View 3: Radar Plot Points (Circle of Scope)
CREATE OR REPLACE VIEW v_circle_radar AS
SELECT 
    s.id AS signal_id,
    s.title,
    s.signal_type,
    s.origin_channel,
    a.name AS actor_name,
    s.scope_distance,
    s.uncertainty_score,
    s.scope_status,
    s.resolution,
    s.estimated_kpi_impact,
    COALESCE(m.delta_value, 0.0) AS latency_delta_ms,
    s.created_at
FROM chat_signals s
JOIN actors a ON s.actor_id = a.id
LEFT JOIN metric_observations m ON s.id = m.signal_id
ORDER BY s.scope_distance ASC;

-- Analytical View 4: Channel Chatter Breakdown
CREATE OR REPLACE VIEW v_channel_chatter AS
SELECT 
    s.origin_channel,
    COUNT(s.id) AS total_signals,
    ROUND(AVG(s.uncertainty_score), 2) AS avg_uncertainty,
    COUNT(CASE WHEN s.scope_status = 'INSIDE_CIRCLE' THEN 1 END) AS inside_circle_count,
    COUNT(CASE WHEN s.scope_status = 'OUTSIDE_CIRCLE' THEN 1 END) AS outside_circle_count,
    COUNT(CASE WHEN s.resolution = 'UNDER_DEBATE' THEN 1 END) AS pending_debates
FROM chat_signals s
GROUP BY s.origin_channel
ORDER BY total_signals DESC;
"""
