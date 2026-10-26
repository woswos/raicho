UPDATE connector_credentials
SET revoked = 1, revision = revision + 1
WHERE identifier = 1 AND revoked = 0;
