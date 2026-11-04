UPDATE browser_sessions
SET last_used_at = ?
WHERE token_digest = ?;
