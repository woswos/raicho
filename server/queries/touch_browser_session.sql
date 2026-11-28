UPDATE browser_sessions
SET last_used_at = max(last_used_at, ?)
WHERE token_digest = ?;
