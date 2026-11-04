DELETE FROM browser_sessions
WHERE token_digest NOT IN (
        SELECT token_digest
        FROM browser_sessions
        ORDER BY created_at DESC, token_digest ASC
        LIMIT ?
    );
