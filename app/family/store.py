"""The family tables.

Applied by ``db.init_db`` straight after the main schema, so they exist on
every database -- a fresh one and one that predates family accounts alike.
Everything here hangs off ``users`` or ``family_parents`` with ON DELETE
CASCADE, so removing a child account or a whole family leaves nothing behind.
"""
from __future__ import annotations

SCHEMA = """
-- A parent or guardian.  Not a player: no avatar, no inventory, no profile.
CREATE TABLE IF NOT EXISTS family_parents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL,
    username_lower  TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    display_name    TEXT NOT NULL DEFAULT '',
    email           TEXT NOT NULL DEFAULT '',
    email_lower     TEXT NOT NULL DEFAULT '',
    relation        TEXT NOT NULL DEFAULT 'parent',
    timezone        TEXT NOT NULL DEFAULT '',
    tz_offset       INTEGER NOT NULL DEFAULT 0,
    created_at      INTEGER NOT NULL,
    last_login      INTEGER NOT NULL DEFAULT 0,
    last_seen       INTEGER NOT NULL DEFAULT 0,
    setup_state     TEXT NOT NULL DEFAULT 'new',
    prefs           TEXT NOT NULL DEFAULT '{}',
    source          TEXT NOT NULL DEFAULT '{}',
    is_disabled     INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_family_parents_email ON family_parents(email_lower);

-- Parent sign-ins.  Kept apart from the players' sessions so a parent and a
-- child can both be signed in on the same family computer at once.
CREATE TABLE IF NOT EXISTS family_sessions (
    token       TEXT PRIMARY KEY,
    parent_id   INTEGER NOT NULL REFERENCES family_parents(id) ON DELETE CASCADE,
    csrf        TEXT NOT NULL,
    created_at  INTEGER NOT NULL,
    expires_at  INTEGER NOT NULL,
    user_agent  TEXT NOT NULL DEFAULT '',
    ip          TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_family_sessions_parent ON family_sessions(parent_id);

-- The link between a child's player account and the parent who made it.
-- Private to that parent; see the package docstring.
CREATE TABLE IF NOT EXISTS family_children (
    user_id     INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    parent_id   INTEGER NOT NULL REFERENCES family_parents(id) ON DELETE CASCADE,
    first_name  TEXT NOT NULL DEFAULT '',
    birth_year  INTEGER NOT NULL DEFAULT 0,
    slot        INTEGER NOT NULL DEFAULT 0,
    controls    TEXT NOT NULL DEFAULT '{}',
    paused      INTEGER NOT NULL DEFAULT 0,
    created_at  INTEGER NOT NULL,
    updated_at  INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_family_children_parent ON family_children(parent_id);

-- Seconds played, by the family's own calendar: one row per child, day,
-- hour and world.  The day totals drive the limit, the hours drive the
-- "when do they play" heat map, the worlds drive the breakdown.
CREATE TABLE IF NOT EXISTS family_playtime (
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day       TEXT NOT NULL,
    hour      INTEGER NOT NULL DEFAULT 0,
    world_id  TEXT NOT NULL,
    seconds   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, day, hour, world_id)
);

-- One row per stretch of play in one world, for the sessions timeline.
CREATE TABLE IF NOT EXISTS family_play_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    world_id    TEXT NOT NULL,
    started_at  INTEGER NOT NULL,
    ended_at    INTEGER NOT NULL,
    seconds     INTEGER NOT NULL DEFAULT 0,
    ended_by    TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_family_play_log_user ON family_play_log(user_id, id DESC);

-- Things a parent should know about: Safe Chat stepping in, a limit
-- reached, a friend waiting for an OK.
CREATE TABLE IF NOT EXISTS family_alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind        TEXT NOT NULL,
    severity    TEXT NOT NULL DEFAULT 'info',
    channel     TEXT NOT NULL DEFAULT '',
    title       TEXT NOT NULL,
    detail      TEXT NOT NULL DEFAULT '',
    excerpt     TEXT NOT NULL DEFAULT '',
    other_name  TEXT NOT NULL DEFAULT '',
    world_id    TEXT NOT NULL DEFAULT '',
    created_at  INTEGER NOT NULL,
    seen_at     INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_family_alerts_user ON family_alerts(user_id, id DESC);

-- Friendships waiting on a parent's OK.  'in': the child accepted somebody
-- else's request.  'out': the child asked somebody.  One row per pair; a
-- later ask refreshes it.
CREATE TABLE IF NOT EXISTS family_approvals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    other_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    direction   TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'waiting',
    created_at  INTEGER NOT NULL,
    decided_at  INTEGER NOT NULL DEFAULT 0,
    UNIQUE (child_id, other_id)
);
CREATE INDEX IF NOT EXISTS idx_family_approvals_waiting ON family_approvals(child_id, status);
"""
