SELECT name
FROM sqlite_schema
WHERE type = 'table' AND name NOT GLOB 'sqlite_*';
