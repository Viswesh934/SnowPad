"""Autonomous Provisioning Engine for Switch Console & Switch Rooms.

This module provisions:
1. The SnowPad Scope Governor agent in Switch PostgreSQL database.
2. The 3 core Switch engineering rooms (product-ideas, backend-core, frontend-chatter).
3. Binds SnowPad to each room and populates realistic chat uncertainty audits.
4. Registers the SnowPad project workspace into Switch Console's local SQLite database.
"""

import asyncio
import os
import sys
import uuid
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

TENANT_ID = '00000000-0000-0000-0000-000000000000'
WORKSPACE_ID = '9e15c987-87e0-4992-91a4-936c182b55df'
ADMIN_USER_ID = '79f221ad-6c25-44ab-b6d6-d31d5b658385'
API_KEY_ID = '7dd53124-9feb-4d54-933d-67c691dcc719'

NOW = datetime.now(timezone.utc)
NOW_STR = NOW.strftime('%Y-%m-%d %H:%M:%S')


def provision_sqlite() -> None:
    """Register SnowPad local workspace and agent in Switch Console SQLite."""
    appdata = os.environ.get("APPDATA", "")
    db_path = os.path.join(appdata, "switchdash", "switchdash.db")
    if not os.path.exists(db_path):
        print(f"[!] Switchdash SQLite DB not found at: {db_path} (Switch Console might not be installed)")
        return

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    loc_id = 'snowpad-local-loc-01'
    project_root = str(Path(__file__).resolve().parent.parent.parent)

    cur.execute('''
        INSERT OR REPLACE INTO locations (id, name, ssh_host, dir, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?);
    ''', (loc_id, 'SnowPad Workspace', None, project_root, NOW_STR, NOW_STR))

    agent_id = 'snowpad-app-agent-01'
    cur.execute('''
        INSERT OR REPLACE INTO agents (
            id, location_id, name, provider_id, switch_agent_id, api_endpoint,
            workspace_id, status, auto_approve, owner_name, provider_config,
            created_at, updated_at, auto_mode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    ''', (
        agent_id,
        loc_id,
        'SnowPad Scope Governor',
        'antigravity',
        'snowpad-governor-agent',
        'http://localhost:55439',
        WORKSPACE_ID,
        'ready',
        1,
        'visweshsigireddy',
        '{}',
        NOW_STR,
        NOW_STR,
        1
    ))

    con.commit()
    con.close()
    print("✔ Switch Console SQLite (locations & agents) provisioned.")


async def provision_postgres() -> None:
    """Register SnowPad agent, rooms, and dialogues in Switch Core PostgreSQL."""
    try:
        import asyncpg
    except ImportError:
        switch_packages = r"F:\gojo\Switch Console\resources\local-server\switch\site-packages"
        if os.path.exists(switch_packages) and switch_packages not in sys.path:
            sys.path.append(switch_packages)
        try:
            import asyncpg
        except ImportError:
            print("[!] asyncpg not found. Run with Switch python or pip install asyncpg.")
            return

    conn = await asyncpg.connect('postgresql://postgres:IOnbPj0kqpXgfLLKlLM6uQTsDMqDQCcN@127.0.0.1:55441/switch')

    # 1. Ensure 3 Rooms exist
    rooms_data = [
        ("product-ideas", "Product roadmap proposals, customer feature requests, and PRD debates"),
        ("backend-core", "Infrastructure discussions, database locks, and performance SLAs"),
        ("frontend-chatter", "UI design discussions, animation proposals, and styling whims")
    ]
    for rname, rdesc in rooms_data:
        rid = str(uuid.uuid4())
        await conn.execute('''
            INSERT INTO rooms (
                id, matrix_room_id, name, description, admin_mode,
                read_visibility, write_visibility, tenant_id, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (tenant_id, matrix_room_id) DO NOTHING;
        ''', rid, f"!{rname}:localhost", rname, rdesc, False, "public", "public", TENANT_ID, NOW)

    rooms = await conn.fetch('SELECT id, name FROM rooms WHERE tenant_id = $1', TENANT_ID)
    room_map = {r['name']: r['id'] for r in rooms}

    # 2. Register Client for SnowPad
    client_id = 'snowpad-client-01'
    await conn.execute('''
        INSERT INTO clients (
            id, matrix_user_id, display_name, type, config, created_at, tenant_id
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (id) DO UPDATE SET display_name = EXCLUDED.display_name;
    ''', client_id, '@snowpad:localhost', 'SnowPad Governor', 'agent', 'null', NOW, TENANT_ID)

    # 3. Register Agent in PostgreSQL
    agent_id = 'snowpad-governor-agent'
    await conn.execute('''
        INSERT INTO agents (
            id, name, description, connector_type, integration_profile,
            client_id, api_key_id, owner_id, display_name, tenant_id,
            agent_type, can_manage_agents, created_at
        ) VALUES (
            $1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10, $11, $12, $13
        ) ON CONFLICT (id) DO UPDATE SET
            display_name = EXCLUDED.display_name,
            description = EXCLUDED.description,
            client_id = EXCLUDED.client_id;
    ''', 
        agent_id, 
        'snowpad', 
        'Autonomous Scope Governor & Tech Debt Radar', 
        'cli', 
        '{"protocol": "stdio", "command": "python -m snowpad.cli bridge"}',
        client_id,
        API_KEY_ID,
        ADMIN_USER_ID,
        'SnowPad Governor',
        TENANT_ID,
        'scope_governor',
        False,
        NOW
    )
    print("✔ SnowPad Agent registered in Switch PostgreSQL.")

    # 4. Bind SnowPad to all 3 rooms
    for r in rooms:
        await conn.execute('''
            INSERT INTO room_agents (
                room_id, agent_id, last_connected_at, alias, receives_join_events, tenant_id
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (room_id, agent_id) DO NOTHING;
        ''', r['id'], agent_id, NOW, 'SnowPad', True, TENANT_ID)

    print(f"✔ SnowPad bound to {len(rooms)} Switch Rooms ({', '.join(room_map.keys())}).")

    # 5. Populate Room Messages
    sample_dialogues = [
        (
            room_map.get('backend-core'),
            ADMIN_USER_ID,
            "Alex Chen",
            "What if we rewrite the entire database ingestion layer in Rust and introduce Kafka this sprint?",
            client_id,
            "SnowPad Governor",
            "🛰️ **[SnowPad Scope Radar] Uncertainty: 84% (HIGH)**\n\n- **Verdict:** `OUTSIDE_CIRCLE (Parked Whim)`\n- **Risk Evaluation:** High tech debt drift. Est. 42h speculative rewrite violating Q4 latency SLAs.\n- **Action:** Diverted to Whim Quarantine. Feature rejected from active sprint scope."
        ),
        (
            room_map.get('frontend-chatter'),
            ADMIN_USER_ID,
            "Sarah Jenkins",
            "Could we add custom WebGL particle animations to the checkout button for extra delight?",
            client_id,
            "SnowPad Governor",
            "🛰️ **[SnowPad Scope Radar] Uncertainty: 91% (HIGH)**\n\n- **Verdict:** `OUTSIDE_CIRCLE (Parked Whim)`\n- **Risk Evaluation:** Bundle bloat (+140KB), zero conversion correlation, maintenance burden.\n- **Action:** Parked into Whim Quarantine. Preserving dev focus on core sprint goals."
        ),
        (
            room_map.get('product-ideas'),
            ADMIN_USER_ID,
            "Michael Chang",
            "/snowpad radar",
            client_id,
            "SnowPad Governor",
            "🛰️ **[Circle of Scope Radar Status]**\n\n- **Active Blips:** 3 Speculative Whims quarantined | 1 Feature Locked\n- **Sprint Health:** 94.2% Stability Index\n- **Tech Debt Savings:** ~68 developer hours saved this week\n- **Next Scheduled Audit:** Tomorrow at 09:00 UTC"
        )
    ]

    for rid, u_sender_id, u_sender_name, u_text, b_sender_id, b_sender_name, b_text in sample_dialogues:
        if not rid:
            continue

        existing_count = await conn.fetchval('SELECT count(*) FROM messages WHERE room_id = $1', rid)
        if existing_count and existing_count > 0:
            continue

        seq = 1
        # User msg
        msg_id_1 = str(uuid.uuid4())
        ev_id_1 = f"${uuid.uuid4()}:localhost"
        await conn.execute('''
            INSERT INTO messages (
                id, seq, room_id, transport_event_id, sender_id, sender_name,
                event_type, msgtype, body, formatted_body, content, sent_at, tenant_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb, $12, $13)
            ON CONFLICT (room_id, seq) DO NOTHING;
        ''', msg_id_1, seq, rid, ev_id_1, u_sender_id, u_sender_name,
           'm.room.message', 'm.text', u_text, u_text, json.dumps({'body': u_text, 'msgtype': 'm.text'}), NOW, TENANT_ID)
        seq += 1

        # Bot msg
        msg_id_2 = str(uuid.uuid4())
        ev_id_2 = f"${uuid.uuid4()}:localhost"
        await conn.execute('''
            INSERT INTO messages (
                id, seq, room_id, transport_event_id, sender_id, sender_name,
                event_type, msgtype, body, formatted_body, content, sent_at, tenant_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb, $12, $13)
            ON CONFLICT (room_id, seq) DO NOTHING;
        ''', msg_id_2, seq, rid, ev_id_2, b_sender_id, b_sender_name,
           'm.room.message', 'm.text', b_text, b_text, json.dumps({'body': b_text, 'msgtype': 'm.text'}), NOW, TENANT_ID)

    print("✔ Switch Room conversation history and audit dialogues populated.")
    await conn.close()


def run_provisioning():
    """Entry point for Switch setup."""
    if len(sys.argv) > 1 and sys.argv[1] == "--pg-only":
        asyncio.run(provision_postgres())
        return

    print("❄️ Provisioning SnowPad Agent & Rooms for Switch Console...")
    provision_sqlite()

    bundled_py = r"F:\gojo\Switch Console\resources\local-server\python\python.exe"
    bundled_site = r"F:\gojo\Switch Console\resources\local-server\switch\site-packages"
    this_script = str(Path(__file__).resolve())

    if os.path.exists(bundled_py) and os.path.exists(bundled_site):
        import subprocess
        cmd = [bundled_py, this_script, "--pg-only"]
        env = os.environ.copy()
        env["PYTHONPATH"] = bundled_site
        res = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if res.stdout:
            print(res.stdout.strip())
        if res.stderr and "Traceback" in res.stderr:
            print("[Postgres Error]", res.stderr.strip())
    else:
        asyncio.run(provision_postgres())

    print("\n🎉 SnowPad is fully connected to Switch! In Switch Console, press Ctrl+R to view your Rooms.")


if __name__ == '__main__':
    run_provisioning()
