CREATE TABLE connector_credentials (
    identifier INTEGER PRIMARY KEY CHECK (identifier = 1),
    backend_kind TEXT NOT NULL CHECK (backend_kind = 'thunderbird'),
    token_digest BLOB NOT NULL CHECK (
        TYPEOF(token_digest) = 'blob' AND LENGTH(token_digest) = 32
    ),
    revoked INTEGER NOT NULL DEFAULT 0 CHECK (revoked IN (0, 1)),
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision > 0)
);
