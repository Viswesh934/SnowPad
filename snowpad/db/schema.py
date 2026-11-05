"""DuckDB Schema DDL and Analytical Views for SnowPad."""

SCHEMA_DDL = """
-- 1. Actors: Developers, PMs, Operators mapped in SnowPad
CREATE TABLE IF NOT EXISTS actors (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    team VARCHAR NOT NULL DEFAULT 'Core Engineering',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Pulse Events: Developer actions, hotfixes on a whim, optimizations
CREATE TABLE IF NOT EXISTS pulse_events (
    id VARCHAR PRIMARY KEY,
    actor_id VARCHAR NOT NULL REFERENCES actors(id),
    event_type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    description VARCHAR,
    commit_hash VARCHAR,
    service_name VARCHAR NOT NULL DEFAULT 'api-gateway',
    scope_status VARCHAR NOT NULL DEFAULT 'INSIDE_CIRCLE',
    scope_distance DOUBLE NOT NULL DEFAULT 0.5,
    tech_debt_flag BOOLEAN DEFAULT FALSE,
    tech_debt_severity VARCHAR DEFAULT 'NONE',
    rationale VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Metric Observations: Performance telemetry, latency deltas, p95/p99 response times
CREATE TABLE IF NOT EXISTS metric_observations (
    id VARCHAR PRIMARY KEY,
    event_id VARCHAR REFERENCES pulse_events(id),
    metric_name VARCHAR NOT NULL DEFAULT 'p95_response_time_ms',
    service_name VARCHAR NOT NULL DEFAULT 'api-gateway',
    endpoint VARCHAR NOT NULL DEFAULT '/api/v1/checkout',
    baseline_value DOUBLE NOT NULL,
    observed_value DOUBLE NOT NULL,
    delta_value DOUBLE NOT NULL,
    unit VARCHAR DEFAULT 'ms',
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Decision Records: Outcomes from team triage discussions (via Switch / chat)
CREATE TABLE IF NOT EXISTS decision_records (
    id VARCHAR PRIMARY KEY,
    event_id VARCHAR NOT NULL REFERENCES pulse_events(id),
    author_id VARCHAR NOT NULL REFERENCES actors(id),
    discussion_summary VARCHAR NOT NULL,
    resolution VARCHAR NOT NULL DEFAULT 'SCHEDULE_REFACTOR',
    target_sprint VARCHAR,
    ttl_days INTEGER DEFAULT 14,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytical View 1: Weekly Developer Pulse
CREATE OR REPLACE VIEW v_weekly_pulse AS
SELECT 
    date_trunc('week', e.created_at) AS pulse_week,
    a.id AS actor_id,
    a.name AS actor_name,
    a.role AS actor_role,
    COUNT(e.id) AS total_events,
    COUNT(CASE WHEN e.event_type = 'HOTFIX' THEN 1 END) AS hotfixes_count,
    COUNT(CASE WHEN e.scope_status = 'INSIDE_CIRCLE' THEN 1 END) AS inside_circle_count,
    COUNT(CASE WHEN e.scope_status = 'OUTSIDE_CIRCLE' THEN 1 END) AS outside_circle_count,
    COUNT(CASE WHEN e.tech_debt_flag = TRUE THEN 1 END) AS tech_debt_logged,
    ROUND(AVG(m.delta_value), 2) AS avg_latency_delta_ms,
    ROUND(MIN(m.delta_value), 2) AS max_latency_improvement_ms
FROM actors a
JOIN pulse_events e ON a.id = e.actor_id
LEFT JOIN metric_observations m ON e.id = m.event_id
GROUP BY 1, 2, 3, 4;

-- Analytical View 2: Developer Quarterly Impact (The "Brag Sheet" & Perf Review view)
CREATE OR REPLACE VIEW v_developer_impact AS
SELECT 
    a.id AS actor_id,
    a.name AS actor_name,
    a.role AS actor_role,
    a.team,
    COUNT(DISTINCT e.id) AS total_contributions,
    COUNT(DISTINCT CASE WHEN e.event_type = 'HOTFIX' THEN e.id END) AS hotfixes_shipped,
    COUNT(DISTINCT CASE WHEN e.event_type = 'PERF_OPTIMIZATION' THEN e.id END) AS perf_optimizations,
    COUNT(DISTINCT CASE WHEN e.scope_status = 'INSIDE_CIRCLE' THEN e.id END) AS high_impact_circle_count,
    COUNT(DISTINCT CASE WHEN e.scope_status = 'OUTSIDE_CIRCLE' THEN e.id END) AS low_leverage_churn_count,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN e.scope_status = 'INSIDE_CIRCLE' THEN e.id END) / 
        NULLIF(COUNT(DISTINCT e.id), 0), 
        1
    ) AS circle_focus_percentage,
    COUNT(DISTINCT CASE WHEN e.tech_debt_flag = TRUE THEN e.id END) AS debt_items_incurred,
    ROUND(COALESCE(AVG(m.delta_value), 0.0), 2) AS avg_latency_impact_ms,
    ROUND(COALESCE(SUM(CASE WHEN m.delta_value < 0 THEN ABS(m.delta_value) ELSE 0 END), 0.0), 1) AS total_ms_shaved
FROM actors a
LEFT JOIN pulse_events e ON a.id = e.actor_id
LEFT JOIN metric_observations m ON e.id = m.event_id
GROUP BY a.id, a.name, a.role, a.team;

-- Analytical View 3: Radar Plot Points (Circle of Scope)
CREATE OR REPLACE VIEW v_circle_radar AS
SELECT 
    e.id AS event_id,
    e.title,
    e.event_type,
    e.service_name,
    a.name AS actor_name,
    e.scope_distance,
    e.scope_status,
    e.tech_debt_flag,
    e.tech_debt_severity,
    COALESCE(m.delta_value, 0.0) AS latency_delta_ms,
    e.created_at
FROM pulse_events e
JOIN actors a ON e.actor_id = a.id
LEFT JOIN metric_observations m ON e.id = m.event_id
ORDER BY e.scope_distance ASC;
"""
