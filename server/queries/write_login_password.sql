INSERT INTO login_password (identifier, password_hash, changed_at)
VALUES (1, ?, ?)
ON CONFLICT (identifier) DO UPDATE
SET password_hash = excluded.password_hash, changed_at = excluded.changed_at;
