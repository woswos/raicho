UPDATE connector_credentials
SET stored_key = ?, server_key = ?, revoked = 0, revision = revision + 1
WHERE identifier = 1 AND revoked = 1;
