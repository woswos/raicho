CREATE TABLE connector_credentials (
    identifier INTEGER PRIMARY KEY CHECK (identifier = 1),
    backend_kind TEXT NOT NULL CHECK (backend_kind = 'thunderbird'),
    stored_key BLOB NOT NULL CHECK (
        TYPEOF(stored_key) = 'blob' AND LENGTH(stored_key) = 32
    ),
    server_key BLOB NOT NULL CHECK (
        TYPEOF(server_key) = 'blob' AND LENGTH(server_key) = 32
    ),
    revoked INTEGER NOT NULL DEFAULT 0 CHECK (revoked IN (0, 1)),
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision > 0)
);
