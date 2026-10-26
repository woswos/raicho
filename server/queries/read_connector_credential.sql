SELECT
    stored_key,
    server_key,
    revoked
FROM connector_credentials
WHERE identifier = 1;
