DELETE FROM browser_sessions
WHERE expires_at <= ? OR last_used_at <= ?;
