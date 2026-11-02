INSERT INTO preferences (name, value)
VALUES (?, ?)
ON CONFLICT (name) DO UPDATE SET value = excluded.value;
