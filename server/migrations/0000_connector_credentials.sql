CREATE TABLE connector_credentials (
    identifier integer PRIMARY KEY CHECK (identifier = 1),
    backend_kind text NOT NULL CHECK (backend_kind = 'thunderbird'),
    stored_key blob NOT NULL CHECK (
        typeof(stored_key) = 'blob' AND length(stored_key) = 32
    ),
    server_key blob NOT NULL CHECK (
        typeof(server_key) = 'blob' AND length(server_key) = 32
    ),
    revoked integer NOT NULL DEFAULT 0 CHECK (revoked IN (0, 1)),
    revision integer NOT NULL DEFAULT 1 CHECK (revision > 0)
);
