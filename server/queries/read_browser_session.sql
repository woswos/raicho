SELECT
    last_used_at,
    expires_at
FROM browser_sessions
WHERE token_digest = ?;
