CREATE TABLE login_password (
    identifier integer PRIMARY KEY CHECK (identifier = 1),
    password_hash text NOT NULL CHECK (
        typeof(password_hash) = 'text' AND length(password_hash) BETWEEN 1 AND 512
    ),
    changed_at integer NOT NULL
);

CREATE TABLE browser_sessions (
    token_digest blob PRIMARY KEY CHECK (
        typeof(token_digest) = 'blob' AND length(token_digest) = 32
    ),
    created_at integer NOT NULL,
    last_used_at integer NOT NULL CHECK (last_used_at >= created_at),
    expires_at integer NOT NULL CHECK (expires_at > created_at)
) WITHOUT ROWID;

CREATE TABLE preferences (
    name text PRIMARY KEY CHECK (name IN ('theme')),
    value text NOT NULL CHECK (
        name != 'theme' OR value IN ('system', 'light', 'dark')
    )
) WITHOUT ROWID;
